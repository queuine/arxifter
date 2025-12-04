#!/bin/sh
#
# Downloads RSS feeds from bioRχiv and LLM-indexes them.
#

cd ./back;

DATADIRBASE="../data/"
FEEDURLBASE="https://connect.biorxiv.org/biorxiv_xml.php?subject="
RSSFILENAME="feed.rss"
TXTFILENAME="feed.txt"
FEEDDOCSDIR="docs"
FEEDVECSDIR="vecs"
LLMKEYFILENAME="../keys/llm_key.txt"

SUBJECTS=`python -m arxifter list subjects`

for item in ${SUBJECTS}; do
    mkdir -p ${DATADIRBASE}${item}
    RSSFILEPATH=${DATADIRBASE}${item}/${RSSFILENAME}
    rm -f ${RSSFILEPATH}
    rm -f ${ITEMDIR}/${FEEDDOCSDIR}/*.json
    wget -O ${RSSFILEPATH} ${FEEDURLBASE}${item} >/dev/null 2>&1
    python -m arxifter parse ${RSSFILEPATH}
    sleep 1
done

export OPENAI_API_KEY=`cat ${LLMKEYFILENAME} | tr -d '[:space:]'`

for item in ${SUBJECTS}; do
    ITEMDIR=${DATADIRBASE}${item}
    rm -f ${ITEMDIR}/${FEEDVECSDIR}/*.json
    python -m arxifter index ${ITEMDIR}
done
