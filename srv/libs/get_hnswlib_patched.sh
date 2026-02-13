#!/bin/sh
#
# Taking, patching and compiling hnswlib.
# Some additional packages might need to be installed:
#
# apt update && apt install -y wget patch diffutils g++
# pip install pybind11
#

RELEASE_FILE="hnswlib-0.8.0.tar.gz"
RELEASE_DIR="hnswlib-0.8.0"
PATCHES_DIR="hnswlib-patches"
FINAL_DIR="hnswlib"

wget -O ${RELEASE_FILE} "https://github.com/nmslib/hnswlib/archive/refs/tags/v0.8.0.tar.gz"
tar xzf ${RELEASE_FILE}

find ${PATCHES_DIR} -type f -name *.patch -exec sh -c 'patch -p0 < "$1"' sh {} \;
mv ${RELEASE_DIR} ${FINAL_DIR}

cd ${FINAL_DIR}
python setup.py build_ext --build-lib .
strip hnswlib.cpython*.so

