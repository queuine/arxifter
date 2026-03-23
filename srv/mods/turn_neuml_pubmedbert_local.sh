#!/bin/bash
#
# The NeuML/pubmedbert-base-embeddings LLM is claimed to be suitable
# for embeddings of life-sciences texts.
#
# This script makes it available for use via the fastembed library.
# Notice that a manual check of presifting results has not found
# an increase in reasonability of the presifted articles though.
#
# It exports the non-ONNX NeuML/pubmedbert-base-embeddings model
# to ONNX format, along with decreasing FP precision, here to fp16.
#
# It requires the optimum and sentence-transformers to be installed.
# pip install torch --index-url https://download.pytorch.org/whl/cpu
# pip install optimum[onnx] sentence-transformers
#

# It expects that HF_HOME env variable is set to the current directory.
export HF_HOME=`pwd`

BASEDIR="./hub"
LIBRARY="sentence_transformers"
DTYPE="fp16"
SOURCE="NeuML/pubmedbert-base-embeddings"
LOCAL="models--local--neuml-pubmedbert-base-embeddings-fp16"
# SNAPSHOT=`python -c "import os, binascii; print(binascii.hexlify(os.urandom(20)).decode('utf8'))"`
SNAPSHOT="63d44a1116283f00768eb9c97636b9f83ededc84"

MODELDIR=${BASEDIR}/${LOCAL}
REFSDIR=${MODELDIR}/refs
SNAPDIR=${MODELDIR}/snapshots/${SNAPSHOT}

mkdir -p ${REFSDIR}
echo -n ${SNAPSHOT} >> ${REFSDIR}/main

mkdir -p ${SNAPDIR}
optimum-cli export onnx --model ${SOURCE} --dtype ${DTYPE} --library-name ${LIBRARY} ${SNAPDIR}/

SPECCONTENT="[fastembed]
pooled = true
normailzed = true
embed_dim = 768
model_file = \"model.onnx\""

echo "${SPECCONTENT}" >> ${MODELDIR}/info.toml

