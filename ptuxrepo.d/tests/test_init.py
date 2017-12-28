import fixture
import os
import stat


class TestInitEmpty(fixture.InEmptyRepo):
    def testDefaultDist(self):
        'A freshly initialized repository has a Packages file'

        self.assertTrue(os.path.isfile('dists/master/main/binary-amd64/Packages'))

    def testPermissions(self):
        'Created repository has setgit and group-writeability'

        mask = 0775 + stat.S_ISGID
        st = os.stat('dists/master/main')
        self.assertEqual(st.st_mode & mask, mask)

    def testDbPermissions(self):
        'DB has group-writeability'

        mask = 0o664
        st = os.stat('.ptuxrepo/db/CURRENT')
        self.assertEqual(st.st_mode & mask, mask)
