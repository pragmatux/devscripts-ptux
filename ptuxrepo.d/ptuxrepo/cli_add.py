'''usage: ptuxrepo add [options] [<repository> [<ingestables>...]]

options:
    --dist <dist>        use <dist> instead of the default distribution
    --dist-force <dist>  force creation of <dist> if it does not exist

Add package(s) to a package repository. With no arguments, add the package(s)
specified in the current .changes file to the default repository. The current
.changes file, found in the parent of the working directory, is selected
according the package version in the head entry of debian/changelog.

A repository other than the default may be specified on the command line. The
default repository is taken from the environment variable PTUXREPO_DIR. Remote
repositories are accessed via the ssh protocol, and specified in the ssh URI
syntax used by git-fetch(1):

    <repository> := ssh://[user@]host.tld[:port]/path/to/repo

or git's scp-like syntax:

    <repository> := [user@]host.tld:path/to/repo

The default distribution of the repository is used unless an alternative is
specified with the option -d. It is an error if the distribution does not
exist, unless the option -f is given, in which case the distribution is
created.
'''


import docopt, sys, os, tempfile, re, subprocess, signal, ptuxrepo


def main(argv):
    args = docopt.docopt(__doc__, argv=argv)

    repo = args['<repository>']
    if repo is None:
        try:
            repo = os.environ['PTUXREPO_REPO']
        except KeyError:
            raise RuntimeError('must give <repository> argument or set PTUXREPO_REPO')

    ingestables = args['<ingestables>']
    for i in ingestables:
        if i.endswith('.changes') or i.endswith('.deb'):
            if os.path.isfile(i):
                continue
            else:
                raise RuntimeError('cannot read file: %s' % i)
        else:
            raise RuntimeError('unsupported file type: %s' % i)
    if not ingestables:
        ingestables = [ptuxrepo.find_changes()]

    m = re.match(r'ssh://(?P<repo>[^:/]+):?(?P<port>[0-9]*)(?P<path>/.*)', repo)
    if m is not None:
        remote = m.group('repo')
        path = m.group('path')
        if path == '':
            path = '.'
        port = m.group('port')
        if port == '':
            port = '22'
    else:
        remote = None
        path = repo

    if remote is None:
        if args['--dist-force']:
            do_local(path, ingestables, dist=args['--dist-force'], create_dist=True)
        else:
            do_local(path, ingestables, dist=args['--dist'])
    else:
        do_remote(remote, port, path, ingestables, args['--dist'], args['--dist-force'])


def do_local(path, ingestables, dist=None, create_dist=False):
    repo = ptuxrepo.Repo(path)

    override = repo.get_script('add')
    if override:
        os.execv(override, sys.argv)

    if create_dist:
        repo.dist_create(dist, force=True)

    output = repo.add(ingestables, dist)
    print output,


def do_remote(remote, port, path, ingestables, dist=None, dist_force=False):
    agent_pid = None
    try:
        # optinally start custom ssh-agent with private key
        key = os.environ.get('PTUXREPO_PRIVATE_KEY')
        if key:
            null = file(os.devnull, 'wb')
            env = subprocess.check_output(['ssh-agent', '-s'])
            environ_amend(env)
            agent_pid = int(os.environ['SSH_AGENT_PID'])
            with tempfile.NamedTemporaryFile() as keyfile:
                keyfile.write(key)
                keyfile.flush()
                subprocess.check_output( ['ssh-add', keyfile.name], stderr=subprocess.STDOUT)

        # send files to server via tar
        files = []
        for i in ingestables:
            files.append(i)
            if i.endswith('.changes'):
                files += ptuxrepo.find_files(i)
        tar_cmd = ['tar', 'cz'] + files
        tar = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)

        # run ptuxrepo-add on server via ssh
        remote_cmd = ['ptuxrepo', 'add', path] + ingestables
        if dist_force:
            remote_cmd[2:2] = ['--dist-force', dist_force]
        elif dist:
            remote_cmd[2:2] = ['--dist', dist]

        remote_script = '''
            set -e
            tmp=$(mktemp -d ptuxrepo-add.XXXXXXXXXX)
            trap "rm -rf $tmp" EXIT
            (cd $tmp && \
                tar xz && \
                PATH=/home/rkuester/ptux/devscripts-ptux/src:$PATH {remote_cmd})
            '''.format(remote_cmd=' '.join(remote_cmd))
        ssh_cmd = ['ssh', '-p', port, remote, remote_script]
        if key:
            ssh_cmd[1:1] = ['-o', 'stricthostkeychecking=no']
        ssh = subprocess.Popen(ssh_cmd,
                               stdin=tar.stdout,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

        tar.stdout.close() # lets tar rx SIGPIPE if ssh exits first
        if tar.wait() != 0:
            raise Exception('tar failed')

        out, err = ssh.communicate()
        if ssh.returncode == 0:
            print out,
        else:
            raise RuntimeError(err)

    finally:
        if agent_pid:
            os.kill(agent_pid, signal.SIGTERM)


def environ_amend(s):
    'Parse VBL=value pairs and add to os.environ'
    pairs = re.findall('SSH_.+=[^;]+', s)
    for vbl, value in [p.split('=') for p in pairs]:
        os.environ[vbl] = value
