"""
Manipulate ptuxrepo configuration files.

usage:
    ptuxrepo config edit [--user]
    ptuxrepo config dump
    ptuxrepo config find

commands:
    edit    open EDITOR on the most local config file, creating if necessary
    dump    dump the current configuration
    find    show the paths at which configuration files are found

options:
    --user  operate on the user-level configuration file, $HOME/.ptuxrepo.conf
"""

example='''\
# {}
# ptuxrepo configuration in YAML

# default:
#     repository: examplerepo
#
# repositories:
#     examplerepo: ssh://user@foo.bar:2222/path/to
'''


from docopt import docopt
import os, os.path, subprocess, yaml, ptuxrepo, config


def main(argv):
    args = docopt(__doc__, argv=argv)

    if args['edit']:
        edit(args)
    elif args['dump']:
        dump(args)
    elif args['find']:
        find(args)


def edit(args):
    if args['--user']:
        path = os.path.join(os.environ['HOME'], config.dotname)
    elif os.path.exists('.git'):
        path = config.gitname
    else:
        path = config.dotname

    editor = os.environ['EDITOR']

    if not os.path.isfile(path):
        with file(path, 'w') as f:
            f.write(example.format(path))

    subprocess.call((editor, path))


def dump(args):
    c = config.read()
    print yaml.dump(c),


def find(args):
    for c in config.candidates():
        try:
            with file(c):
                print c
        except IOError:
            pass
