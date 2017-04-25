import fixture
import os


class Dist(fixture.InEmptyRepo):
    def test_add(self):
        'adds a distribution'

        fixture.cli('dist', 'testdist')
        self.assertTrue(os.path.isfile('dists/testdist/main/binary-amd64/Packages'))


    def test_force(self):
        '--force <dist> does not error if <dist> exists'

        fixture.cli('dist', 'testdist')
        fixture.cli('dist', '--force', 'testdist')


    def test_list(self):
        'lists distributions'

        with fixture.stdout(fixture.cli, 'dist') as out:
            self.assertEqual(out, 'master\n')
