'''Common configuration file handling for ptuxrepo.

The following paths are searched for configuration files. Values from paths
down the list override those from paths up the list.

  * $HOME/.ptuxrepo.conf
  * $PWD/.git/ptuxrepo.conf
  * $PWD/.ptuxrepo.conf


The configuration file is in YAML syntax.

----
default:
    repo: local

repos:
    sdk:
        url: ssh://rkuester@packages.pragmatux.org:2223/sdk
        default-dist: stretch

    device:
        url: ssh://rkuester@packages.pragmatux.org:2223/device

    local:
        path: /home/rkuester/local-repo
        default-dist: testing
----
'''


import yaml
import os
import os.path
import re


basename = 'ptuxrepo.conf'
dotname = '.' + basename
gitname = os.path.join('.git', basename)


def candidates(bottom=None):
    '''Yield a sequence of candidate configuration file paths, beginning with
    the most general and ending with the most specific. The values in more
    specific files overwrite the values in more general files.'''

    if bottom is None:
        bottom = os.getcwd()

    try:
        home = os.environ['HOME']
        yield os.path.join(home, dotname)
    except KeyError:
        pass

    p = os.path.realpath(bottom)
    yield os.path.join(p, gitname)
    yield os.path.join(p, dotname)


def read():
    paths = candidates()
    merged = {}
    for p in paths:
        try:
            with file(p) as f:
                config = yaml.safe_load(f)
            merged.update(config)
        except IOError:
            pass

    return merged


def get(keys, default=None):
    'Recursively lookup a value in a tree of dictionaries.'

    v = read()
    for k in keys:
        try:
            v = v[k]
        except:
            return default

    return v


class URL:
    '''A repository URL with the following attributes:
    authority
    path
    port '''

    def __init__(self, url):
        'Parse a URL from the given string.'

        m = re.match(r'ssh://(?P<auth>[^:/]+):?(?P<port>[0-9]*)(?P<path>/.*)', url)
        if m:
            self.authority = m.group('auth')
            self.path = m.group('path')
            if self.path == '':
                self.path = '.'
            self.port = m.group('port')
            if self.port == '':
                self.port = '22'
        else:
            raise ValueError('not a valid repository URL')


class Repository:
    '''A Repository has the following attributes:
    url
    path
    default_dist (may be None) '''

    def __init__(self, path=None, url=None, default_dist=None):
        if path and url:
            raise ValueError('both path and url cannot be set')
        self.path = path
        self.url = url
        self.default_dist = default_dist


def get_repository(name):
    'Get a Repository defined in the configuration files.'

    conf = get(('repos', name))
    if conf:
        try:
            if 'url' in conf:
                url = URL(conf['url'])
            else:
                url = None

            path = conf.get('path')
            default_dist = conf.get('default-dist')

            return Repository(path=path, url=url, default_dist=default_dist)

        except AttributeError:
            raise ValueError('repo {} ill defined in config'.format(name))

    else:
        return None


def choose_repository(arg):
    '''Choose a Repository based on <arg>, config, and defaults.

    1. <arg> is a name found in config files
    2. <arg> is a URL
    3. <arg> is None, try name or URL in environ['PTUXREPO_REPO']
    4. <arg> is None, try default in config'''

    spec = arg
    if spec is None:
        spec = os.environ.get('PTUXREPO_REPO')
        if spec is None:
            spec = get(('default', 'repo'))
            if spec is None:
                raise Exception('no repository given, in PTUXREPO_REPO, or in config')

    repo = get_repository(spec)
    if repo is None:
        try:
            url = URL(spec)
            repo = Repository(url=url)
        except ValueError:
            repo = Repository(path=spec)

    return repo
