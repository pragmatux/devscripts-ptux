import fixture
import os


class TestInitEmpty(fixture.InEmptyRepo):
    def testDefaultDist(self):
        'A freshly initialized repository has a Packages file'

        self.assertTrue(os.path.isfile('dists/master/main/binary-amd64/Packages'))
