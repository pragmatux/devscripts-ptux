#!/usr/bin/env python
"""
usage: ptuxrepo [--help] [--debug] <command> [<args>...]

options:
   -h, --help  print this help
   --debug     print extra debugging output

commands:
   init  initialize a repository
   dist  list and create distributions
   add   add packages and changes to a distribution
"""


from docopt import docopt
import sys
from importlib import import_module


def hide_traceback(type, value, traceback):
    if type is RuntimeError:
        sys.stderr.write("error: %s\n" % value)
    else:
        sys.__excepthook__(type, value, traceback)


def main(argv=sys.argv[1:]):
    args = docopt(__doc__, argv=argv, options_first=True)

    if not args['--debug']:
        sys.excepthook = hide_traceback

    cmd = import_module('.cli_%s' % args['<command>'], 'ptuxrepo')
    cmd.main([args['<command>']] + args['<args>'])
