import subprocess, re, os, json, tempfile, debian.changelog, debian.deb822, debian.debfile, stat
from contextlib import contextmanager


@contextmanager
def umask(new):
    try:
        old = os.umask(new)
        yield
    finally:
        os.umask(old)

def we_own(path):
    st = os.stat(path)
    uid = os.getuid()
    return st.st_uid == uid


def fixup_db_perms(db):
    '''Add group permission to aptly db files, which aptly creates without
       group permission no matter the umask.'''
    for dirpath, dirs, files in os.walk(db):
        if we_own(dirpath):
            os.chmod(dirpath, 0o2775)
        for f in [os.path.join(dirpath, x) for x in files]:
            if we_own(f):
                os.chmod(f, 0o664)


class AptlyClient(object):
    def __init__(self, path):
        self.path = path

        cfg = {
            'rootDir': path,
            'keyring': os.path.join(path, 'trustedkeys.gpg'),
            'gpgDisableSign': True,
            'gpgDisableVerify': True,
            'downloadSourcePackages': True,
        }
        with tempfile.NamedTemporaryFile(prefix='ptuxrepo-conf', delete=False) as self.config:
            json.dump(cfg, self.config)

        self.env = os.environ.copy()
        self.env['PATH'] = '/usr/lib/ptuxrepo/aptly:' + self.env['PATH']

    def __del__(self):
        os.unlink(self.config.name)

    def call(self, *args):
        try:
            with umask(0002):
                cmd = ['aptly', '-config=%s' % self.config.name] + list(args)
                return subprocess.check_output(cmd, env=self.env)
        except subprocess.CalledProcessError as e:
            print e.output
            raise
        finally:
            db = os.path.join(self.path, 'db')
            fixup_db_perms(db)

    def repo_list(self):
        output = self.call('repo', 'list')
        return re.findall('\[(.*)\]', output)

    def repo_create(self, name, dist):
        self.call('repo', 'create', '-distribution=%s' % dist, name)

    def repo_remove(self, name, pattern):
        output = self.call('repo', 'remove', name, pattern)
        return output

    def repo_add(self, deb, name):
        output = self.call('repo', 'add', '-remove-files=false', name, deb)
        return output

    def repo_include(self, changes, name):
        output = self.call('repo', 'include', '-repo=%s' % name, '-accept-unsigned=true', '-no-remove-files=true', changes)
        return output

    def publish_repo(self, name):
        self.call('publish', 'repo', '-architectures=amd64,armhf,armel,source', '-origin=Pragmatux', name)

    def publish_update(self, name):
        self.call('publish', 'update', name)

    def db_cleanup(self):
        self.call('db', 'cleanup')


class Repo(object):
    def __init__(self, path, default_dist=None, initialize=False):
        self.path = path
        self.default_dist = default_dist
        self.aptly = None

        if initialize:
            if default_dist is None:
                self.default_dist = 'master'
            self._initialize()

        versionfile = self.privpath('version')
        if not os.path.isfile(versionfile):
            raise RuntimeError('incompatible repo at %s' % versionfile)

    def _initialize(self):
        'Initialize the repository on disk.'

        with umask(0002):
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            elif not os.path.isdir(self.path):
                raise RuntimeError('cannot create repo at path %s' % self.path)
            os.chmod(self.path, 0775 | stat.S_ISGID)

            os.makedirs(self.privpath('scripts'))
            os.symlink('..', self.privpath('public'))

            with file(self.privpath('version'), 'w') as f:
                f.write('2')

            with file(self.privpath('default-dist'), 'w') as f:
                f.write(self.default_dist)

        self.dist_create(self.default_dist)

    def privpath(self, rel=None):
        'Return an absolute path within the private directory.'
        privdir = os.path.join(self.path, '.ptuxrepo')
        if rel:
            return os.path.join(privdir, rel)
        else:
            return privdir

    def get_aptly(self):
        if self.aptly is None:
            self.aptly = AptlyClient(self.privpath())
        return self.aptly

    def get_default_dist(self):
        if self.default_dist is None:
            with file(self.privpath('default-dist')) as f:
                self.default_dist = f.read()
        return self.default_dist

    def get_script(self, name):
        filename = os.path.join(self.privpath('scripts'), name)
        if os.path.isfile(filename):
            return filename
        else:
            return None

    def dist_create(self, name, force=False):
        aptly = self.get_aptly()
        repos = aptly.repo_list()
        if name not in repos:
            aptly.repo_create(name, dist=name)
            aptly.publish_repo(name)
        else:
            if not force:
                raise Exception('dist "%s" already exists' % name)

    def dist_list(self):
        aptly = self.get_aptly()
        return aptly.repo_list()

    def add(self, ingestables, dist=None):
        if dist is None:
            dist = self.get_default_dist()
        aptly = self.get_aptly()

        for i in ingestables:
            if i.endswith('.deb'):
                ctrl = debian.debfile.DebFile(i).debcontrol()
                obsoletes = '%s, !$Version (= %s)' % (ctrl['package'], ctrl['version'])
                out = aptly.repo_add(i, dist)

            elif i.endswith('.changes'):
                with file(i) as f:
                    changes = debian.deb822.Changes(f)
                obsoletes = '%s, !$Version (= %s)' % (changes['Source'], changes['Version'])
                out = aptly.repo_include(i, dist)

            else:
                raise Exception('invalid file type added: %s' % i)

            out += aptly.repo_remove(dist, obsoletes)

        aptly.publish_update(dist)

        post_add_hook = self.get_script('post-add')
        if post_add_hook:
            out += subprocess.check_output([post_add_hook] + ingestables)

        return out


def find_buildfile(basename, srcdir):
    searchpath = ['..', 'debian/build']
    paths = [os.path.join(s, basename) for s in searchpath]
    for p in paths:
        if os.path.isfile(p):
            return p
    else:
        raise IOError('cannot find file %s' % name)


def find_changes(srcdir=None):
    if srcdir is None:
        srcdir = os.getcwd()
    path = os.path.join(srcdir, 'debian/changelog')
    with file(path) as f:
        changelog = debian.changelog.Changelog(f)
    basename = '%s_%s_amd64.changes' % (changelog.package, changelog.version)
    return find_buildfile(basename, srcdir)


def find_files(changes_path):
    files = []
    base = os.path.dirname(changes_path)

    with file(changes_path) as f:
        changes = debian.deb822.Changes(f)

    for name in [f['name'] for f in changes['files']]:
        path = os.path.join(base, name)
        files.append(path)

    return files
