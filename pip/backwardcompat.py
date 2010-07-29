"""Stuff that isn't in some old versions of Python"""

import sys
import os
import shutil

__all__ = ['any', 'WindowsError', 'md5', 'copytree']

try:
    WindowsError = WindowsError
except NameError:
    WindowsError = None
try:
    from hashlib import md5
except ImportError:
    import md5 as md5_module
    md5 = md5_module.new

try:
    from pkgutil import walk_packages
except ImportError:
    # let's fall back as long as we can
    from _pkgutil import walk_packages

try:
    any = any
except NameError:

    def any(seq):
        for item in seq:
            if item:
                return True
        return False


def copytree(src, dst):
    if sys.version_info < (2, 5):
        before_last_dir = os.path.dirname(dst)
        if not os.path.exists(before_last_dir):
            os.makedirs(before_last_dir)
        shutil.copytree(src, dst)
        shutil.copymode(src, dst)
    else:
        shutil.copytree(src, dst)


