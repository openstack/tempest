#!/bin/bash
TOOLS=`dirname $0`
VENV=$TOOLS/../.kong-venv
source $VENV/bin/activate && $@
