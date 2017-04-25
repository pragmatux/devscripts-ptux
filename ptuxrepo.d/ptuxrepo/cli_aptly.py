'''usage: ptuxrepo aptly <args>...

Call the aptly backend, passing through <args>. Assume the aptly repository is
in the current directory.
'''


import docopt, sys, os, tempfile, re, subprocess, signal, ptuxrepo


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    repo = ptuxrepo.Repo('.')
    aptly = repo.get_aptly()
    argseq = args['<args>']
    print aptly.call(*argseq)
