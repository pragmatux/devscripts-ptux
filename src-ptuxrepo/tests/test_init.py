import fixture
import os
import stat


class TestInitEmpty(fixture.InEmptyRepo):
    def testDefaultDist(self):
        'A freshly initialized repository has a Packages file'

        self.assertTrue(os.path.isfile('dists/master/main/binary-amd64/Packages'))

    def testPermissions(self):
        'has setgit and group-writeability'

        mask = 0775 + stat.S_ISGID
        st = os.stat('dists/master/main')
        self.assertEqual(st.st_mode & mask, mask)
