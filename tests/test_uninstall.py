
import textwrap
from os.path import join
from tempfile import mkdtemp
from test_pip import here, reset_env, run_pip, pyversion, lib_py, get_env, diff_states, write_file

site_pkg = join(lib_py, 'site-packages')
easy_install_pth = join(site_pkg, 'easy-install.pth')

def test_1():
    '''
    Simple install and uninstall::
    '''
    reset_env()
    result = run_pip('install', 'INITools==0.2', expect_error=True)
    assert join(site_pkg, 'initools') in result.files_created, sorted(result.files_created.keys())
    result2 = run_pip('uninstall', 'INITools', '-y', expect_error=True)
    assert diff_states(result.files_before, result2.files_after, ignore=['build']).values() == [{}, {}, {}]

def test_2():
    '''
    Uninstall an easy_installed package with scripts::
    '''
    reset_env()
    env = get_env()
    result = env.run(join(env.base_path, 'bin', 'easy_install'), 'PyLogo')
    assert('PyLogo' in result.files_updated[easy_install_pth].bytes), result.files_after[easy_install_pth].bytes
    result2 = run_pip('uninstall', 'pylogo', '-y', expect_error=True)
    assert diff_states(result.files_before, result2.files_after, ignore=['build']).values() == [{}, {}, {}]

def test_3():
    '''
    Uninstall a distribution with a namespace package without clobbering
    the namespace and everything in it::
    '''
    reset_env()
    result = run_pip('install', 'pd.requires==0.0.3', expect_error=True)
    assert join(site_pkg, 'pd') in result.files_created, sorted(result.files_created.keys())
    result2 = run_pip('uninstall', 'pd.find', '-y', expect_error=True)
    assert join(site_pkg, 'pd') not in result2.files_deleted, sorted(result2.files_deleted.keys())
    assert join(site_pkg, 'pd', 'find') in result2.files_deleted, sorted(result2.files_deleted.keys())

def test_4():
    '''
    Uninstall a package with more files (script entry points, extra directories)::
    '''
    reset_env()
    result = run_pip('install', 'virtualenv', expect_error=True)
    assert ('bin/virtualenv') in result.files_created, sorted(result.files_created.keys())
    result2 = run_pip('uninstall', 'virtualenv', '-y', expect_error=True)
    assert diff_states(result.files_before, result2.files_after, ignore=['build']).values() == [{}, {}, {}]

def test_5():
    '''
    Same, but easy_installed::
    '''
    reset_env()
    env = get_env()
    result = env.run(join(env.base_path, 'bin', 'easy_install'), 'virtualenv')
    assert ('bin/virtualenv') in result.files_created, sorted(result.files_created.keys())
    result2 = run_pip('uninstall', 'virtualenv', '-y', expect_error=True)
    assert diff_states(result.files_before, result2.files_after, ignore=['build']).values() == [{}, {}, {}]

def test_6():
    '''
    Uninstall an editable installation from svn::
    '''
    reset_env()
    result = run_pip('install', '-e', 'svn+http://svn.colorstudy.com/INITools/trunk#egg=initools-dev', expect_error=True)
    egg_link = result.files_created[join(site_pkg, 'INITools.egg-link')]
    result2 = run_pip('uninstall', '-y', 'initools', expect_error=True)
    assert ('src/initools' in result2.files_after), 'oh noes, pip deleted my sources!'
    assert diff_states(result.files_before, result2.files_after, ignore=['src/initools', 'build']).values() == [{}, {}, {}]

def test_7():
    '''
    Editable install from existing source outside the venv::
    '''
    tmpdir = mkdtemp()
    reset_env()
    env = get_env()
    result = env.run('hg', 'clone', 'http://bitbucket.org/ianb/virtualenv/', tmpdir)
    result2 = run_pip('install', '-e', tmpdir)
    assert (join(site_pkg, 'virtualenv.egg-link') in result2.files_created), result2.files_created.keys()
    result3 = run_pip('uninstall', '-y', 'virtualenv', expect_error=True)
    assert diff_states(result.files_before, result3.files_after, ignore=['build']).values() == [{}, {}, {}]

def test_8():
    '''
    Uninstall from a requirements file::
    '''
    reset_env()
    write_file('test-req.txt', textwrap.dedent('''\
        -e svn+http://svn.colorstudy.com/INITools/trunk#egg=initools-dev
        # and something else to test out:
        PyLogo<0.4
        '''))
    result = run_pip('install', '-r', 'test-req.txt')
    result2 = run_pip('uninstall', '-r', 'test-req.txt', '-y')
    assert diff_states(result.files_before, result2.files_after, ignore=['build', 'src/initools']).values() == [{}, {}, {}]

