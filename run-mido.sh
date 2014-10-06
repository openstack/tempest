#!/bin/sh
nosetests -v \
tempest.scenario.midokura.test_network_advanced_inter_vmconnectivity \
tempest.scenario.midokura.test_network_advanced_metadata.py \
tempest.scenario.midokura.test_network_advanced_security_groups \
tempest.scenario.midokura.test_network_advanced_security_groups_2networks \
tempest.scenario.midokura.test_network_basic_adminstateup \
tempest.scenario.midokura.test_network_basic_dhcp_disable \
tempest.scenario.midokura.test_network_basic_dhcp_lease \
tempest.scenario.midokura.test_network_basic_inter_vmconnectivity \
tempest.scenario.midokura.test_network_basic_metadata \
tempest.scenario.midokura.test_network_basic_multisubnet \
tempest.scenario.midokura.test_network_basic_security_groups \
tempest.scenario.midokura.test_network_basic_security_groups_2networks \
tempest.scenario.midokura.test_network_basic_security_groups_netcat \
tempest.scenario.midokura.test_network_basic_vmconnectivity \
2>&1 | tee mido-results-`date +%Y%m%d-%H%M`.log
