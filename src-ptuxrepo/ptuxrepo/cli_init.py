"""
Create a ptuxrepo APT repository in $PWD or <dir>.

usage:
    ptuxrepo init [-h] [<dir>]

options:
    -h, --help  print this help
"""


from docopt import docopt
import os, ptuxrepo


def main(argv):
    args = docopt(__doc__, argv=argv)
    path = args['<dir>']
    if path is None:
        path = os.environ.get('PTUXREPO_DIR', '.')

    if os.path.exists(path):
        if os.path.isdir(path) and not os.listdir(path):
            pass
        else:
            raise RuntimeError('path %s exists and is not an empty directory' % path)

    ptuxrepo.Repo(path, initialize=True)
