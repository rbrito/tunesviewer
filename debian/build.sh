#!/bin/sh

git checkout debian

SNAPSHOT=$(git describe --tags)
VERSION=$(echo $SNAPSHOT | sed -e 's/-.*//' | sed -e 's/^v//')
PROGRAM=tunesviewer

git checkout fixes
git archive --prefix=${PROGRAM}-${SNAPSHOT}/ -o ../${PROGRAM}_${VERSION}.orig.tar.gz HEAD

git checkout debian
fakeroot debian/rules clean binary
