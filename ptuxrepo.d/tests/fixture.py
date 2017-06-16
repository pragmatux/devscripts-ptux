import unittest
import tempfile
import os
import shutil
import sys
from cStringIO import StringIO
from contextlib import contextmanager
import debian.deb822
import ptuxrepo.cli


def cli(*args):
    return ptuxrepo.cli.main(args)


class DummyPackage:
    def __init__(self, version='1.0'):
        self.name    = 'dummy'
        self.version = version
        self.deb     = self.abspath('dummy/dummy_{}_all.deb'.format(version))
        self.dsc     = self.abspath('dummy/dummy_{}.dsc'.format(version))
        self.dir     = self.abspath('dummy/dummy-{}'.format(version))
        self.changes = self.abspath('dummy/dummy_{}_amd64.changes'.format(version))

    def abspath(self, relpath):
        base = os.path.dirname(__file__)
        return os.path.join(base, relpath)


class Repo(object):
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix='ptuxrepo-')
        cli('init', self.path)

    def close(self):
        shutil.rmtree(self.path)

    def has_binary(self, pkg, dist='master'):
        packages = os.path.join(self.path, 'dists/%s/main/binary-amd64/Packages' % dist)
        with file(packages) as f:
            for p in debian.deb822.Packages.iter_paragraphs(f):
                if p['package'] == pkg.name and p['version'] == pkg.version:
                    return True
            else:
                return False


class InEmptyRepo(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        os.chdir(self.repo.path)

    def tearDown(self):
        self.repo.close()

    def tree(self):
        import subprocess
        subprocess.call(('tree', '-s', '.'))

    def assert_has_binary(self, pkg, dist='master'):
        self.assertTrue(self.repo.has_binary(pkg, dist))

    def assert_no_binary(self, pkg, dist='master'):
        self.assertFalse(self.repo.has_binary(pkg, dist))


@contextmanager
def stdout(command, *args, **kwargs):
    save = sys.stdout
    sys.stdout = StringIO()
    try:
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
    finally:
        sys.stdout = save


@contextmanager
def cwd(newdir):
    olddir = os.getcwd()
    try:
        os.chdir(newdir)
        yield
    finally:
        os.chdir(olddir)


@contextmanager
def tempdir():
    try:
        d = tempfile.mkdtemp(prefix='ptuxrepo-')
        yield d
    finally:
        shutil.rmtree(d)


@contextmanager
def tempcwd():
    with tempdir() as d:
        with cwd(d):
            yield
