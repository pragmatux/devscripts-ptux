"""
List or create a distributions.

usage:
    ptuxrepo dist
    ptuxrepo dist [--force] <name>

options:
    -h, --help   print this help
    -f, --force  no error if the distribution already exists
"""


from docopt import docopt
import os, ptuxrepo


def main(argv):
    args = docopt(__doc__, argv=argv)
    name = args['<name>']

    path = os.environ.get('PTUXREPO_DIR', '.')
    repo = ptuxrepo.Repo(path)

    if name:
        repo.dist_create(name, force=args['--force'])
    else:
        for d in repo.dist_list():
            print d
