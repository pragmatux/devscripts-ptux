#!/usr/bin/env python
"""
usage: ptuxversion [options] [<commit-ish>]

options:
  --check-development   return 0 if not released, otherwise 1
"""


import sys
from docopt import docopt
from ptuxutil import sh
from ptuxutil.sh.contrib import git
import time
import string


def _distance(commit, base=None):
    if base:
        arg = '{}..{}'.format(base, commit)
    else:
        arg = commit

    count = git('rev-list', '--count', arg)
    return int(count)


def _are_synonomous(c1, c2):
    diff = git('rev-list', '{}...{}'.format(c1, c2))
    return not bool(diff)


def _is_dirty():
    modified = git('ls-files', '--modified', '--others', '--exclude-standard')
    return bool(modified)


def _is_contained(commit, by):
    if not by: return False
    excess = git('rev-list', commit, '^{}'.format(by))
    return not bool(excess)


def _strip_vendor(tag):
    vendor, sep, basetag = tag.rpartition('/')
    return basetag


def _unmangle_tag(tag):
    'Unmangle a tag name according to DEP14'
    tab = {ord('%'): ord(':'), ord('_'): ord('~'), ord('#'): None}
    return tag.translate(tab)


def _nearest_tag(commit, limit=None, patterns=['*']):
    try:
        args = ['--tags']
        args += ['--abbrev=0']
        args += ['--match={}'.format(p) for p in patterns]
        args += [commit]
        tag = git.describe(*args).strip()
    except sh.ErrorReturnCode:
        return None

    if limit:
        if not _is_contained(limit, by=tag):
            return None

    return tag


def tag_plus_distance(commit, base=None):
    tag = _nearest_tag(commit, base)
    if tag:
        t = _strip_vendor(_unmangle_tag(tag))
        d = _distance(commit, tag)
        return '{}+{}'.format(t, d) if d else t
    else:
        return str(_distance(commit, base))


def _is_valid(commit):
    try:
        sha = git('rev-parse', '--verify', '{}^{{commit}}'.format(commit))
    except sh.ErrorReturnCode_128:
        return False

    return True


def _nearest_published(commit):
    if _is_valid('origin/master'):
        base = git('merge-base', commit, 'origin/master').strip()
    elif _is_valid('master'):
        base = git('merge-base', commit, 'master').strip()
    else:
        base = None

    return _nearest_tag(commit, base) or base


def is_development(commit):
    return (_are_synonomous(commit, 'HEAD') and _is_dirty()) \
           or not _is_contained(commit, _nearest_published(commit))


def describe(commit='HEAD'):
    y = ''
    if _are_synonomous(commit, 'HEAD') and _is_dirty():
        y = '~dirty'

    n = _nearest_published(commit)

    t = ''
    if y or not _is_contained(commit, n):
        sec_since_epoch = int(time.time())
        t = '+T{}'.format(sec_since_epoch)

    d = tag_plus_distance(n) if n else '0'
    r = git('rev-parse', '--short', commit).strip()

    return '{}{}~g{}{}'.format(d, t, r, y)


def cli(argv=sys.argv[1:]):
    args = docopt(__doc__, argv=argv)
    commit = args['<commit-ish>'] or 'HEAD'

    if args['--check-development']:
        if is_development(commit):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print describe(commit)


if __name__ == "__main__":
    cli()
