
from test_pip import here, reset_env, run_pip, pyversion, lib_py

def test_1():
    '''
    First a test of the distutils-configuration-setting command (which is distinct from other commands)::
    '''
    #print run_pip('-vv', '--distutils-cfg=easy_install:index_url:http://download.zope.org/ppix/', expect_error=True)
    #Script result: python ../../poacheggs.py -E .../poacheggs-tests/test-scratch -vv --distutils-cfg=easy_install:index_url:http://download.zope.org/ppix/
    #-- stdout: --------------------
    #Distutils config .../poacheggs-tests/test-scratch/lib/python.../distutils/distutils.cfg is writable
    #Replaced setting index_url
    #Updated .../poacheggs-tests/test-scratch/lib/python.../distutils/distutils.cfg
    #<BLANKLINE>
    #-- updated: -------------------
    #  lib/python2.4/distutils/distutils.cfg  (346 bytes)

def test_2():
    '''
    Next, a simple test::
    '''
    reset_env()
    result = run_pip('install', '-vvv', 'INITools==0.2', expect_error=True)
    assert (lib_py + 'site-packages/INITools-0.2-py%s.egg-info' % pyversion) in result.files_created, str(result) #sorted(result.files_created.keys())
    assert (lib_py + 'site-packages/initools') in result.files_created, sorted(result.files_created.keys())

def test_3():
    '''
    Let's try that again, editable::
    '''
    reset_env()
    result = run_pip('install', '-e', 'INITools==0.2', expect_error=True)
    assert "--editable=INITools==0.2 should be formatted with svn+URL" in result.stdout
    #assert len(result.files_created) == 1, result.files_created # FIXME: what file should be created here?
    assert not result.files_updated, result.files_updated

def test_4():
    '''
    Now, checking out from svn::
    '''
    reset_env()
    result = run_pip('install', '-e', 'svn+http://svn.colorstudy.com/INITools/trunk#egg=initools-dev', expect_error=True)
    egg_link = result.files_created[lib_py + 'site-packages/INITools.egg-link']
    # FIXME: I don't understand why there's a trailing . here:
    assert egg_link.bytes.endswith('/test-scratch/src/initools\n.'), egg_link.bytes
    assert (lib_py + 'site-packages/easy-install.pth') in result.files_updated
    assert 'src/initools' in result.files_created
    assert 'src/initools/.svn' in result.files_created


def test_5():
    '''
    Using package==dev::
    '''
    reset_env()
    result = run_pip('install', 'INITools==dev', expect_error=True)
    assert (lib_py + 'site-packages/initools') in result.files_created, str(result.stdout)

def test_6():
    '''
    Cloning from Git::
    '''
    reset_env()
    result = run_pip('install', '-e', 'git://github.com/jezdez/django-feedutil.git#egg=django-feedutil', expect_error=True)
    egg_link = result.files_created[lib_py + 'site-packages/django-feedutil.egg-link']
    # FIXME: I don't understand why there's a trailing . here:
    assert egg_link.bytes.endswith('/test-scratch/src/django-feedutil\n.'), egg_link.bytes
    assert (lib_py + 'site-packages/easy-install.pth') in result.files_updated
    assert 'src/django-feedutil' in result.files_created
    assert 'src/django-feedutil/.git' in result.files_created

def test_7():
    '''
    Cloning from Mercurial::
    '''
    reset_env()
    result = run_pip('install', '-e', 'hg+http://bitbucket.org/ubernostrum/django-registration/#egg=django-registration', expect_error=True)
    egg_link = result.files_created[lib_py + 'site-packages/django-registration.egg-link']
    # FIXME: I don't understand why there's a trailing . here:
    assert egg_link.bytes.endswith('/test-scratch/src/django-registration\n.'), egg_link.bytes
    assert (lib_py + 'site-packages/easy-install.pth') in result.files_updated
    assert 'src/django-registration' in result.files_created
    assert 'src/django-registration/.hg' in result.files_created

def test_8():
    '''
    Presence or absence of final slash is also normalized::
    '''
    reset_env()
    result = run_pip('install', '-e', 'hg+http://bitbucket.org/ubernostrum/django-registration#egg=django-registration', expect_error=True)
    assert 'pip-log.txt' not in result.files_created, result.files_created['pip-log.txt'].bytes

def test_9():
    '''
    Checking out from Bazaar::
    '''
    reset_env()
    result = run_pip('install', '-e', 'bzr+http://bazaar.launchpad.net/%7Edjango-wikiapp/django-wikiapp/release-0.1/@174#egg=django-wikiapp', expect_error=True)
    egg_link = result.files_created[lib_py + 'site-packages/django-wikiapp.egg-link']
    # FIXME: I don't understand why there's a trailing . here:
    assert egg_link.bytes.endswith('/test-scratch/src/django-wikiapp\n.'), egg_link.bytes
    assert (lib_py + 'site-packages/easy-install.pth') in result.files_updated
    assert 'src/django-wikiapp' in result.files_created
    assert 'src/django-wikiapp/.bzr' in result.files_created

def test_10():
    '''
    Urlquoted characters are normalized for repo URL comparison::
    '''
    reset_env()
    result = run_pip('install', '-e', 'bzr+http://bazaar.launchpad.net/~django-wikiapp/django-wikiapp/release-0.1#egg=django-wikiapp', expect_error=True)
    assert 'pip-log.txt' not in result.files_created, result.files_created['pip-log.txt'].bytes

