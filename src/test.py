import unittest
import tempfile
import os
import shutil
import random
from ptuxutil import sh
from sh import git
import ptuxversion


class Base(unittest.TestCase):
    def setUp(self):
        self.commits = []
        self.olddir = os.getcwd()
        self.repodir = tempfile.mkdtemp(prefix='ptuxversion-test-')
        os.chdir(self.repodir)
        git.init()

    def tearDown(self):
        os.chdir(self.olddir)
        shutil.rmtree(self.repodir)

    def addCommit(self):
        name = str(random.randint(0, 2**20))
        open(name, 'a').close()
        git.add(name)
        git.commit(m=name)
        short = git('rev-parse', '--short', 'HEAD').strip()
        self.commits.append(short)
        return self.commits[-1]


class LocalRepo(Base):
    'In a local repository with no remote'

    def setUp(self):
        Base.setUp(self)
        for _ in range(3): self.addCommit()

    def testClean(self):
        'A clean repository has a version of the form <distance>~g<sha>.'
        version = ptuxversion.describe()
        expect = '{}~g{}'.format(len(self.commits), self.commits[-1])
        self.assertEquals(version, expect)

    def testDirty(self):
        'A dirty repository has a version of the form <distance>+T<seconds>~g<sha>~dirty.'
        open('_', 'a').close()
        version = ptuxversion.describe()
        expect = '{}\+T[0-9]+~g{}~dirty'.format(len(self.commits), self.commits[-1])
        self.assertRegexpMatches(version, expect)

    def testDirtyNotHEAD(self):
        'A version for a commit other than HEAD shall not be dirty.'
        open('_', 'a').close()
        version = ptuxversion.describe('HEAD~1')
        expect = '{}~g{}'.format(len(self.commits) - 1, self.commits[-2])
        self.assertEquals(version, expect)

    def testOffMaster(self):
        'Off branch master, all versions are development'
        master_distance = len(self.commits)
        git.checkout('-b', 'dev')
        for _ in range(2): self.addCommit()
        version = ptuxversion.describe()
        expect = '{}\+T[0-9]+~g{}'.format(master_distance, self.commits[-1])
        self.assertRegexpMatches(version, expect)

    def testTag(self):
        'A version for a commit following a tag has the form <tag>+<distance>~g<sha>'
        tagname = 'tagname'
        git.tag(tagname)
        distance = len(self.commits) + 3
        for _ in range(distance): self.addCommit()
        version = ptuxversion.describe()
        expect = '{}+{}~g{}'.format(tagname, distance, self.commits[-1])
        self.assertEquals(version, expect)

    def testOnTag(self):
        'A version for a commit on a tag has the form <tag>~g<sha>'
        tagname = 'tagname'
        git.tag(tagname)
        version = ptuxversion.describe()
        expect = '{}~g{}'.format(tagname, self.commits[-1])
        self.assertEquals(version, expect)

    def testTagUnmangling(self):
        'Tags are unmangled per DEP14'
        tagname = '2%3_beta.#.1.#'
        unmangled = '2:3~beta..1.'
        git.tag(tagname)
        distance = len(self.commits) + 3
        for _ in range(distance): self.addCommit()
        version = ptuxversion.describe()
        expect = '{}+{}~g{}'.format(unmangled, distance, self.commits[-1])
        self.assertEquals(version, expect)

    def tagWithVendor(self):
        'Vendor prefixes are stripped off tags, e.g.: pragmatux/1.2 --> 1.2'
        tag = '1.2'
        git.tag('pragmatux/' + tag)
        self.addCommit()
        expect = '{}+1~g{}'.format(tag, self.commits[-1])

    def testTagOffMaster(self):
        'Off branch master, master tags are still used with development version'
        tagname = 'tagname'
        git.tag(tagname)
        distance = len(self.commits) + 3
        for _ in range(distance): self.addCommit()
        git.checkout('-b', 'dev')
        for _ in range(2): self.addCommit()
        version = ptuxversion.describe()
        expect = '{}\+{}\+T[0-9]+~g{}'.format(tagname, distance, self.commits[-1])
        self.assertRegexpMatches(version, expect)

    def testTagOffMaster(self):
        'Assume tags off branch master are also published'
        git.checkout('-b', 'dev')
        for _ in range(2): self.addCommit()
        tagname = 'tagname'
        git.tag(tagname)
        distance = 4
        for _ in range(distance): self.addCommit()
        version = ptuxversion.describe()
        expect = '{}\+T[0-9]+~g{}'.format(tagname, self.commits[-1])
        self.assertRegexpMatches(version, expect)


class WithRemote(Base):
    'In a local repository with a remote'

    def setUp(self):
        Base.setUp(self)
        self.addCommit()

        self.remotedir = tempfile.mkdtemp(prefix='ptuxversiont-test-')
        git.init(self.remotedir, bare=True)
        git.remote.add('origin', self.remotedir)
        git.push('-u', 'origin', 'master')

    def tearDown(self):
        shutil.rmtree(self.remotedir)

    def testReleaseVersionIfPushed(self):
        'Version on master is a release version if pushed to origin/master.'
        expect = '{}~g{}'.format(len(self.commits), self.commits[-1])
        version = ptuxversion.describe()
        self.assertEquals(version, expect)

    def testDevopmentIfNotPushed(self):
        'Version on master is a development version if not pushed to origin/master.'
        distance = len(self.commits)
        self.addCommit()
        expect = '{}\+T[0-9]+~g{}'.format(distance, self.commits[-1])
        version = ptuxversion.describe()
        self.assertRegexpMatches(version, expect)
