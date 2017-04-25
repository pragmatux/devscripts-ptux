import fixture


class Aptly(fixture.InEmptyRepo):
    def test_basic(self):
        'aptly command gives basic access to underlying repo'

        with fixture.stdout(fixture.cli, 'aptly', 'repo', 'list') as out:
            self.assertTrue('* [master] (packages' in out)
