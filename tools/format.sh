#!/bin/bash
cd $(dirname "$(readlink -f "$0")")

autopep8 --exit-code --max-line-length=79 --experimental --in-place -r ../tempest ../setup.py && echo Formatting was not needed. >&2

