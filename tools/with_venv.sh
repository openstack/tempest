#!/bin/bash
TOOLS=`dirname $0`
if [ -n "$venv" ]; then
VENV=$venv
else
VENV=$TOOLS/../.venv
fi
source $VENV/bin/activate && "$@"
