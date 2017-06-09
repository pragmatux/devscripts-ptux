# users.sh
#
# Customize users and groups by mounting a file like this over the path
# /users.sh and restarting the container. This file is sourced by /startup.sh.

# List users here. Arrange for their ssh keys to be found in
# /home/$NAME/.ssh/authorized_keys, typically by mounting a volume over /home.
# UIDs are given explicitly so they can be kept stable and synchronized with
# the UIDs used in the storage volume.
#
# user <name> <uid>
user ptuxrepo 2001

# List groups here, and add users to groups as shown.
#
# group <name> <gid>
group uploaders 3001

# Add users to groups
#
# adduser <user> <group>
adduser ptuxrepo uploaders

