import fixture


class Aptly(fixture.InEmptyRepo):
    def test_basic(self):
        'aptly command gives basic access to underlying repo'

        with fixture.stdout(fixture.cli, 'aptly', 'repo', 'list') as out:
            self.assertTrue('* [master] (packages' in out)

    def test_with_options(self):
        'passes options to aptly'

        with fixture.stdout(fixture.cli, 'aptly', 'repo', 'list', '-raw') as out:
            self.assertTrue('master\n' in out)
