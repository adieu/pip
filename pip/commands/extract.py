import sys
import re
import fnmatch
import os
import shutil
import zipfile
from pip.util import display_path, backup_dir
from pip.log import logger
from pip.exceptions import InstallationError
from pip.basecommand import Command

class ExtractCommand(Command):
    name = 'extract'
    usage = '%prog [OPTIONS] PACKAGE_NAMES...'
    summary = 'Extract individual packages'

    def __init__(self):
        super(ExtractCommand, self).__init__()
        self.parser.add_option(
            '--no-pyc',
            action='store_true',
            dest='no_pyc',
            help='Do not include .pyc files in extracted files (useful on Google App Engine)')
        self.parser.add_option(
            '-l', '--list',
            action='store_true',
            dest='list',
            help='List the packages available, and their zip status')
        self.parser.add_option(
            '--sort-files',
            action='store_true',
            dest='sort_files',
            help='With --list, sort packages according to how many files they contain')
        self.parser.add_option(
            '--path',
            action='append',
            dest='paths',
            help='Restrict operations to the given paths (may include wildcards)')
        self.parser.add_option(
            '--dest-path',
            action='store',
            dest='dest_path',
            default=os.getcwd(),
            help='The destination path')
        self.parser.add_option(
            '-n', '--simulate',
            action='store_true',
            help='Do not actually perform the extract operation')

    def paths(self):
        """All the entries of sys.path, possibly restricted by --path"""
        if not self.select_paths:
            return sys.path
        result = []
        match_any = set()
        for path in sys.path:
            path = os.path.normcase(os.path.abspath(path))
            for match in self.select_paths:
                match = os.path.normcase(os.path.abspath(match))
                if '*' in match:
                    if re.search(fnmatch.translate(match+'*'), path):
                        result.append(path)
                        match_any.add(match)
                        break
                else:
                    if path.startswith(match):
                        result.append(path)
                        match_any.add(match)
                        break
            else:
                logger.debug("Skipping path %s because it doesn't match %s"
                             % (path, ', '.join(self.select_paths)))
        for match in self.select_paths:
            if match not in match_any and '*' not in match:
                result.append(match)
                logger.debug("Adding path %s because it doesn't match anything already on sys.path"
                             % match)
        return result

    def run(self, options, args):
        self.select_paths = options.paths
        self.simulate = options.simulate
        self.destination_path = options.dest_path
        if options.list:
            return self.list(options, args)
        if not args:
            raise InstallationError(
                'You must give at least one package to extract')
        packages = []
        for arg in args:
            module_name, filename = self.find_package(arg)
            packages.append((module_name, filename))
        last_status = None
        for module_name, filename in packages:
            last_status = self.extract_package(module_name, filename, options.no_pyc)
        return last_status

    def extract_package(self, module_name, filename, no_pyc):
        orig_filename = filename
        logger.notify('Extract %s (in %s)' % (module_name, display_path(filename)))
        logger.indent += 2
        dest_filename = os.path.join(os.path.abspath(self.destination_path), os.path.basename(filename))
        try:
            logger.info('Extracting file to %s' % display_path(dest_filename))
            if not self.simulate:
                if no_pyc:
                    shutil.copytree(orig_filename, dest_filename, ignore=shutil.ignore_patterns('*.pyc'))
                else:
                    shutil.copytree(orig_filename, dest_filename)
        except:
            ## FIXME: need to do an undo here
            raise
        finally:
            logger.indent -= 2

    def find_package(self, package):
        for path in self.paths():
            full = os.path.join(path, package)
            if os.path.exists(full):
                return package, full
            if not os.path.isdir(path) and zipfile.is_zipfile(path):
                zip = zipfile.ZipFile(path, 'r')
                try:
                    zip.read('%s/__init__.py' % package)
                except KeyError:
                    pass
                else:
                    zip.close()
                    return package, full
                zip.close()
        ## FIXME: need special error for package.py case:
        raise InstallationError(
            'No package with the name %s found' % package)

    def list(self, options, args):
        if args:
            raise InstallationError(
                'You cannot give an argument with --list')
        for path in sorted(self.paths()):
            if not os.path.exists(path):
                continue
            basename = os.path.basename(path.rstrip(os.path.sep))
            if os.path.isfile(path) and zipfile.is_zipfile(path):
                if os.path.dirname(path) not in self.paths():
                    logger.notify('Zipped egg: %s' % display_path(path))
                continue
            if (basename != 'site-packages'
                and not path.replace('\\', '/').endswith('lib/python')):
                continue
            logger.notify('In %s:' % display_path(path))
            logger.indent += 2
            zipped = []
            unzipped = []
            try:
                for filename in sorted(os.listdir(path)):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ('.pth', '.egg-info', '.egg-link'):
                        continue
                    if ext == '.py':
                        logger.info('Not displaying %s: not a package' % display_path(filename))
                        continue
                    full = os.path.join(path, filename)
                    if os.path.isdir(full):
                        unzipped.append((filename, self.count_package(full)))
                    elif zipfile.is_zipfile(full):
                        zipped.append(filename)
                    else:
                        logger.info('Unknown file: %s' % display_path(filename))
                if zipped:
                    logger.notify('Zipped packages:')
                    logger.indent += 2
                    try:
                        for filename in zipped:
                            logger.notify(filename)
                    finally:
                        logger.indent -= 2
                else:
                    logger.notify('No zipped packages.')
                if unzipped:
                    if options.sort_files:
                        unzipped.sort(key=lambda x: -x[1])
                    logger.notify('Unzipped packages:')
                    logger.indent += 2
                    try:
                        for filename, count in unzipped:
                            logger.notify('%s  (%i files)' % (filename, count))
                    finally:
                        logger.indent -= 2
                else:
                    logger.notify('No unzipped packages.')
            finally:
                logger.indent -= 2

    def count_package(self, path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            filenames = [f for f in filenames
                         if not f.lower().endswith('.pyc')]
            total += len(filenames)
        return total

ExtractCommand()
