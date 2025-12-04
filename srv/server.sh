#!/bin/sh

export FLASK_APP=back/app.py
export FLASK_RUN_HOST=0.0.0.0

flask run --debug

