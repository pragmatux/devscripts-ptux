#!/bin/sh
#
# This is an example startup script for the ptuxrepo container. The script
# configures the desired users and groups, and launches a ssh daemon to listen
# for incoming requests. This script is located at /start.sh in the container.

set -e

user () {
	name=$1
	uid=$2

	addgroup --gid $uid $name
	adduser --gecos $name,,, --disabled-password --uid $uid --gid $uid $name
}

group () {
	name=$1
	gid=$2

	addgroup --gid $gid $name
}

# Customize users and groups by mounting a data file over the path /users.sh in
# the container. An example users.sh is provided.
. /users.sh

exec /usr/sbin/sshd -D
