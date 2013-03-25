#!/usr/bin/env bash

python tools/hacking.py --ignore=E122,E125,E126 --repeat --show-source --exclude=.venv,.tox,dist,doc,openstack,*egg .
pep8_ret=$?

pyflakes tempest stress setup.py tools cli bin | grep "imported but unused"
unused_ret=$?

ret=0
if [ $pep8_ret != 0 ]; then
    echo "hacking.py/pep8 test FAILED!" >&2
    (( ret += 1  ))
else
    echo "hacking.py/pep8 test OK!" >&2
fi

if [ $unused_ret == 0 ]; then
    echo "Unused import test FAILED!" >&2
    (( ret += 2  ))
else
    echo "Unused import test OK!" >&2
fi

exit $ret
