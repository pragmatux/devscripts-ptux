import fixture


class Add(fixture.InEmptyRepo):
    def __init__(self, *args):
        super(Add, self).__init__(*args)
        self.dp1 = fixture.DummyPackage('1.0')
        self.dp2 = fixture.DummyPackage('2.0')

    def test_deb(self):
        'adds a .deb file'

        fixture.cli('add', '.', self.dp1.deb)
        self.assert_has_binary(self.dp1)

    def test_changes(self):
        'adds a .changes file'

        fixture.cli('add', '.', self.dp1.changes)
        self.assert_has_binary(self.dp1)

    def test_discover(self):
        'discovers and adds the current .changes file'

        with fixture.cwd(self.dp1.dir):
            fixture.cli('add', self.repo.path)

        self.assert_has_binary(self.dp1)

    def test_replaces(self):
        'add replaces old package versions'

        fixture.cli('add', '.', self.dp1.changes)
        self.assert_has_binary(self.dp1)

        fixture.cli('add', '.', self.dp2.changes)
        self.assert_has_binary(self.dp2)
        self.assert_no_binary(self.dp1)

    def test_force_dist(self):
        'add --dist-force DIST creates new distribution'

        dist = 'testing'
        fixture.cli('add', '--dist-force', dist, '.', self.dp1.changes)
        self.assert_has_binary(self.dp1, dist=dist)

    def test_reponame(self):
        'repo comes from config if name is specified'

        with fixture.tempcwd():
            c = ('repos:\n'
                 '  test/funky:\n'
                 '    path: {}\n'.format(self.repo.path))
            with file('.ptuxrepo.conf', 'w') as f:
                f.write(c)

            fixture.cli('add', 'test/funky', self.dp1.changes)
            self.assert_has_binary(self.dp1)

    def test_reponame(self):
        'repo comes from config default if specified'

        with fixture.tempcwd():
            c = ('default:\n'
                 '  repo: test/funky\n'
                 'repos:\n'
                 '  test/funky:\n'
                 '    path: {}\n'.format(self.repo.path))

            with fixture.cwd(self.dp1.dir):
                with file('.ptuxrepo.conf', 'w') as f:
                    f.write(c)
                fixture.cli('add')

            self.assert_has_binary(self.dp1)
