#!/bin/sh
#
# Prunes the downloaded and indexed feeds.
#

BASEDIR=/arxifter
cd ${BASEDIR}/srv/back;

CONF_PATH=${BASEDIR}/srv/conf/arxifter.toml
CONF_ENV_VAR=`python -m arxifter conf env`
export ${CONF_ENV_VAR}=${CONF_PATH}

python -m arxifter feeds prune

