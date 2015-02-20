#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage ./run-mido.sh [tag]"
    exit 1
fi

./run_tempest.sh tempest.api.network \
    tempest.scenario.test_network_basic_ops \
    tempest.scenario.test_network_advanced_server_ops \
    tempest.scenario.test_security_groups_basic_ops \
    tempest.scenario.midokura 2>&1 | tee test_results_$1_$(date +%Y%d%m-%H%M).log
