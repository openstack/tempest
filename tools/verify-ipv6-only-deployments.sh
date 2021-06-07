#!/bin/bash

# NOTE(yoctozepto): This scripts lives now in devstack where it belongs.
# It is kept here for the legacy (dsvm) jobs which look for it in tempest still.
# TODO: Drop it when no legacy jobs use the master tempest.

DEVSTACK_DIR=$(cd $(dirname "$0")/../../devstack && pwd)
$DEVSTACK_DIR/tools/verify-ipv6-only-deployments.sh
