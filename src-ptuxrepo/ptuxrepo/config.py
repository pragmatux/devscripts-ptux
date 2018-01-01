'''Common configuration file handling for ptuxrepo.

The following paths are searched for configuration files. Values from paths
down the list override those from paths up the list.

  * $HOME/.ptuxrepo.conf
  * $PWD/.git/ptuxrepo.conf
  * $PWD/.ptuxrepo.conf


The configuration file is in YAML syntax.

----
default:
    repository: sdk

repositories:
    sdk:
        uri: ssh://rkuester@jade.insymbols.com:2223/sdk

    device:
        uri: ssh://rkuester@jade.insymbols.com:2223/sdk
----
'''


import yaml
import os
import os.path


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
