#!/bin/sh
TEMPDIR=`mktemp -d`
CFGFILE=tempest.conf.sample
tools/config/generate_sample.sh -b ./ -p tempest -o $TEMPDIR
if ! diff $TEMPDIR/$CFGFILE etc/$CFGFILE
then
    echo "E: tempest.conf.sample is not up to date, please run:"
    echo "MODULEPATH=tempest.common.generate_sample_tempest tools/config/generate_sample.sh"
    exit 42
fi
