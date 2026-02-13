#!/bin/sh
#
# Applying the unique-docs patches.
#

PATCHES_DIR="hnswlib-patches"

find ${PATCHES_DIR} -type f -name *.patch -exec sh -c 'patch -p0 < "$1"' sh {} \;

