#!/bin/sh
#
# Making patches for the hnswlib, so that it supports
# unique doc ids at knn searches.
#

ORIGINAL_DIR="hnswlib-0.8.0"
UPDATED_DIR="hnswlib-updated"
PATCHES_DIR="hnswlib-patches"
PATCHES_SUBDIRS="hnswlib python_bindings"
UPDATED_FILES="
hnswlib/hnswlib.h
hnswlib/hnswalg.h
hnswlib/bruteforce.h
python_bindings/bindings.cpp
python_bindings/LazyIndex.py
"

mkdir ${PATCHES_DIR}
for subdir in ${PATCHES_SUBDIRS}
do
    mkdir ${PATCHES_DIR}/${subdir}
done

for subpath in ${UPDATED_FILES}
do
    diff -u ${ORIGINAL_DIR}/${subpath} ${UPDATED_DIR}/${subpath} > ${PATCHES_DIR}/${subpath}.patch
done

