#!/bin/sh
#
# Downloads API feeds from bioRχiv and LLM-indexes them.
#

BASEDIR=/app/arxifter
cd ${BASEDIR}/srv/back;

CONF_PATH=${BASEDIR}/srv/conf/arxifter.toml
CONF_ENV_VAR=`python -m arxifter conf env`
export ${CONF_ENV_VAR}=${CONF_PATH}

python -m arxifter spans incr

