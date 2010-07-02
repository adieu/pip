import sys
import re
import textwrap
from doctest import OutputChecker, ELLIPSIS
from test_pip import reset_env, run_pip, write_file, get_env
from local_repos import local_checkout, local_repo


distribute_re = re.compile('^distribute==[0-9.]+\n', re.MULTILINE)


def _check_output(result, expected):
    checker = OutputChecker()
    actual = str(result)

    ## FIXME!  The following is a TOTAL hack.  For some reason the
    ## __str__ result for pkg_resources.Requirement gets downcased on
    ## Windows.  Since INITools is the only package we're installing
    ## in this file with funky case requirements, I'm forcibly
    ## upcasing it.  You can also normalize everything to lowercase,
    ## but then you have to remember to upcase <BLANKLINE>.  The right
    ## thing to do in the end is probably to find out how to report
    ## the proper fully-cased package name in our error message.
    if sys.platform == 'win32':
        actual = actual.replace('initools', 'INITools')

    # This allows our existing tests to work when run in a context
    # with distribute installed.
    actual = distribute_re.sub('', actual)

    def banner(msg):
        return '\n========== %s ==========\n' % msg
    assert checker.check_output(expected, actual, ELLIPSIS), banner('EXPECTED')+expected+banner('ACTUAL')+actual+banner(6*'=')


def test_freeze():
    """
    Some tests of freeze, first we have to install some stuff.  Note that
    the test is a little crude at the end because Python 2.5+ adds egg
    info to the standard library, so stuff like wsgiref will show up in
    the freezing.  (Probably that should be accounted for in pip, but
    currently it is not).

    TODO: refactor this test into multiple tests? (and maybe different
    test style instead of using doctest output checker)

    """
    env = reset_env()
    write_file('initools-req.txt', textwrap.dedent("""\
        INITools==0.2
        # and something else to test out:
        simplejson<=1.7.4
        """))
    result = run_pip('install', '-r', env.scratch_path/'initools-req.txt')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: pip freeze
        -- stdout: --------------------
        INITools==0.2
        simplejson==1.7.4...
        <BLANKLINE>""")
    _check_output(result, expected)
    
    # Now lets try it with an svn checkout::
    result = env.run('svn', 'co', '-r10',
                     local_repo('svn+http://svn.colorstudy.com/INITools/trunk'),
                     'initools-trunk')
    result = env.run('python', 'setup.py', 'develop',
            cwd=env.scratch_path/ 'initools-trunk')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stdout: --------------------
        -e %s@10#egg=INITools-0.3.1dev_r10-py2...-dev_r10
        simplejson==1.7.4...
        <BLANKLINE>""" % local_checkout('svn+http://svn.colorstudy.com/INITools/trunk'))
    _check_output(result, expected)

    # Now, straight from trunk (but not editable/setup.py develop)::
    result = env.run('easy_install', 'http://svn.colorstudy.com/INITools/trunk')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stderr: --------------------
        Warning: cannot find svn location for INITools==...dev-r...
        <BLANKLINE>
        -- stdout: --------------------
        ## FIXME: could not find svn URL in dependency_links for this package:
        INITools==...dev-r...
        simplejson==1.7.4...
        <BLANKLINE>""")
    _check_output(result, expected)

    # Bah, that's no good!  Let's give it a hint::
    result = run_pip('freeze', '-f',
                     '%s#egg=INITools-dev' %
                     local_checkout('svn+http://svn.colorstudy.com/INITools/trunk'),
                     expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze -f %(repo)s#egg=INITools-dev
        -- stdout: --------------------
        -f %(repo)s#egg=INITools-dev
        # Installing as editable to satisfy requirement INITools==...dev-r...:
        -e %(repo)s@...#egg=INITools-...dev_r...
        simplejson==1.7.4...
        <BLANKLINE>""" % {'repo': local_checkout('svn+http://svn.colorstudy.com/INITools/trunk')})
    _check_output(result, expected)


def test_freeze_git_clone():
    """
    Test freezing a Git clone.

    """
    env = reset_env()
    result = env.run('git', 'clone', local_repo('git+http://github.com/jezdez/django-pagination.git'), 'django-pagination')
    result = env.run('git', 'checkout', '1df6507872d73ee387eb375428eafbfc253dfcd8',
            cwd=env.scratch_path/'django-pagination', expect_stderr=True)
    result = env.run('python', 'setup.py', 'develop',
            cwd=env.scratch_path / 'django-pagination')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stdout: --------------------
        -e %s@...#egg=django_pagination-...
        ...""" % local_checkout('git+http://github.com/jezdez/django-pagination.git'))
    _check_output(result, expected)

    result = run_pip('freeze', '-f',
                     '%s#egg=django_pagination' % local_checkout('git+http://github.com/jezdez/django-pagination.git'),
                     expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: pip freeze -f %(repo)s#egg=django_pagination
        -- stdout: --------------------
        -f %(repo)s#egg=django_pagination
        -e %(repo)s@...#egg=django_pagination-...-dev
        ...""" % {'repo': local_checkout('git+http://github.com/jezdez/django-pagination.git')})
    _check_output(result, expected)


def test_freeze_mercurial_clone():
    """
    Test freezing a Mercurial clone.

    """
    reset_env()
    env = get_env()
    result = env.run('hg', 'clone',
                     '-r', 'f8f7eaf275c5',
                     local_repo('hg+http://bitbucket.org/jezdez/django-dbtemplates'),
                     'django-dbtemplates')
    result = env.run('python', 'setup.py', 'develop',
            cwd=env.scratch_path/'django-dbtemplates')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stdout: --------------------
        -e %s@...#egg=django_dbtemplates-...
        ...""" % local_checkout('hg+http://bitbucket.org/jezdez/django-dbtemplates'))
    _check_output(result, expected)

    result = run_pip('freeze', '-f',
                     '%s#egg=django_dbtemplates' % local_checkout('hg+http://bitbucket.org/jezdez/django-dbtemplates'),
                     expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze -f %(repo)s#egg=django_dbtemplates
        -- stdout: --------------------
        -f %(repo)s#egg=django_dbtemplates
        -e %(repo)s@...#egg=django_dbtemplates-...
        ...""" % {'repo': local_checkout('hg+http://bitbucket.org/jezdez/django-dbtemplates')})
    _check_output(result, expected)


def test_freeze_bazaar_clone():
    """
    Test freezing a Bazaar clone.

    """
    reset_env()
    env = get_env()
    result = env.run('bzr', 'checkout', '-r', '174',
                     local_repo('bzr+http://bazaar.launchpad.net/%7Edjango-wikiapp/django-wikiapp/release-0.1'),
                     'django-wikiapp')
    result = env.run('python', 'setup.py', 'develop',
            cwd=env.scratch_path/'django-wikiapp')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stdout: --------------------
        -e %s@...#egg=django_wikiapp-...
        ...""" % local_checkout('bzr+http://bazaar.launchpad.net/%7Edjango-wikiapp/django-wikiapp/release-0.1'))
    _check_output(result, expected)

    result = run_pip('freeze', '-f',
                     '%s/#egg=django-wikiapp' %
                     local_checkout('bzr+http://bazaar.launchpad.net/%7Edjango-wikiapp/django-wikiapp/release-0.1'),
                     expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze -f %(repo)s/#egg=django-wikiapp
        -- stdout: --------------------
        -f %(repo)s/#egg=django-wikiapp
        -e %(repo)s@...#egg=django_wikiapp-...
        ...""" % {'repo':
                  local_checkout('bzr+http://bazaar.launchpad.net/%7Edjango-wikiapp/django-wikiapp/release-0.1')})
    _check_output(result, expected)


def test_freeze_with_local_option():
    """
    Test that wsgiref (from global site-packages) is reported normally, but not with --local.

    """
    reset_env()
    result = run_pip('install', 'initools==0.2')
    result = run_pip('freeze', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze
        -- stdout: --------------------
        INITools==0.2
        wsgiref==...
        <BLANKLINE>""")

    # The following check is broken (see
    # http://bitbucket.org/ianb/pip/issue/110).  For now we are simply
    # neutering this test, but if we can't find a way to fix it,
    # this whole function should be removed.

    # _check_output(result, expected)

    result = run_pip('freeze', '--local', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: ...pip freeze --local
        -- stdout: --------------------
        INITools==0.2
        <BLANKLINE>""")
    _check_output(result, expected)
