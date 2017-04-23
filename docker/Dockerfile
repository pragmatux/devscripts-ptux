FROM debian:stretch

LABEL maintainer "Ryan Kuester <rkuester@insymbols.com>"

CMD ["/usr/sbin/sshd", "-D"]

RUN adduser --gecos ptuxrepo,,, --disabled-password --home /ptuxrepo ptuxrepo

ADD ptuxrepo*.deb /tmp

RUN dpkg --unpack /tmp/ptuxrepo*.deb \
 && apt-get -yq update \
 && apt-get -yq --fix-broken install \
 && apt-get -yq install --no-install-recommends openssh-server
