# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


"""
The tests need special image uploaded to glance:
  * It has "Cisco enic" driver installed
  * Configured to log into it with username/password


Before running the tests:
* create 'tempest.conf' file in 'etc' folder (default location)
* add/update following parameters to tempest.conf
* replace parameter values with correct ones for your OS installation

[DEFAULT]
debug = true              # Leave it as is
use_stderr = false        # Leave it as is
log_file = tempest.log    # Leave it as is

[auth]
tempest_roles = _member_          # Leave it as is
allow_tenant_isolation = True     # Leave it as is

[compute]
ssh_auth_method = 'configured'
image_ssh_user = 'root'           # username to log into an instance.
image_ssh_password = 'ubuntu'     # password to log into an instance
flavor_ref = 3 # medium           # flavor id. The flavor should have >= 4Gb of RAM
flavor_ref_alt = 3	# medium    # Same as above
image_ref = 60ad4b1e-c5d4-49ad-a9ca-6374c1d8b3f6      # Image id. Used to boot an instance
image_ref_alt = 60ad4b1e-c5d4-49ad-a9ca-6374c1d8b3f6  # Same as above

[identity]
username = demo               # Leave it as is
tenant_name = demo            # Leave it as is
password = demo               # Leave it as is
alt_username = alt_demo       # Leave it as is
alt_tenant_name = alt_demo    # Leave it as is
alt_password = secrete        # Leave it as is
# There should be OS admin user (with admin role) credentials.
# It will be used by the tests to create another non-admin users
admin_username = admin        # Change it if needed
admin_tenant_name = admin     # Change it if needed
admin_domain_name = Default   # Change it if needed
disable_ssl_certificate_validation = false
uri = http://172.29.173.85:5000/v2.0/                         # Set correct IP address
auth_version = v2
admin_password = 1567c9ff7c66376a333d28dfa1a5a3cd717156c7     # Set correct admin password
uri_v3 = http://172.29.173.85:5000/v3/                        # Set correct IP address
admin_tenant_id = 725d6fa98000418f88e47d283d8f1efb            # Set correct admin tenant id

[service_available]
neutron = True

[network]
public_network_id = 1c87c1d3-bd1a-4738-bd55-99a84fa45c87    # id of your public network

[ucsm]
ucsm_ip=10.30.119.66              # UCSM VIP
ucsm_username=admin               # UCSM username
ucsm_password=cisco               # UCSM ppassword
# Dictionary of <hostname> VS <UCSM service profile name>
ucsm_host_dict=overcloud-controller-0.localdomain:QA2,overcloud-compute-0.localdomain:QA3,overcloud-compute-1.localdomain:QA4
network_node_list=overcloud-controller-0.localdomain, overcloud-controller-1.localdomain  # list of hostnames of a network nodes
eth_names=eth0,eth1
virtual_functions_amount=4    # Amount of "SR-IOV ports"/"Dynamic VNICs"/"Virtual functions"


Use environment variables to set location of "tempest.conf"
Ex:
  export TEMPEST_CONFIG_DIR=/etc/redhat-certification-openstack/
  export TEMPEST_CONFIG=tempest.conf

It is better to create dedicated virtualenv for the tempest:
* Run: 'virtualenv myenv'
* Activate the environment. Run: 'source myenv/bin/activate'
* Install python requirements: Run: 'pip install -r requirements.txt'

Running tests:
* Create testr repository: 'testr init'
* Look for tests: 'testr list-tests | grep cisco'
* Run tests:
    'testr run tempest.thirdparty.cisco.test_ucsm'
"""

import socket

from oslo_log import log
from tempest import config
from tempest.scenario import manager
from tempest.thirdparty.cisco import base as cisco_base

CONF = config.CONF
LOG = log.getLogger(__name__)


class UCSMTest(manager.NetworkScenarioTest, cisco_base.UCSMTestMixin):

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(UCSMTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(UCSMTest, cls).setup_clients()
        cls.admin_networks_client = cls.os_adm.networks_client
        cls.admin_network_client = cls.os_adm.network_client

    @classmethod
    def resource_setup(cls):
        super(UCSMTest, cls).resource_setup()
        super(UCSMTest, cls).ucsm_resource_setup()

    def setUp(self):
        super(UCSMTest, self).setUp()

        socket.setdefaulttimeout(10)
        self.keypairs = {}
        self.servers = []
        self.security_group = \
            self._create_security_group(tenant_id=self.tenant_id)

        # Log into UCS Manager
        self.ucsm_setup()
        self.addCleanup(self.ucsm_cleanup)

    def _delete_network(self, network):
        self.networks_client.delete_network(network['id'])

    def _delete_networks(self, networks):
        for n in networks:
            self._delete_network(n)
        # Asserting that the networks are not found in the list after deletion
        body = self.networks_client.list_networks()
        networks_list = [network['id'] for network in body['networks']]
        for n in networks:
            self.assertNotIn(n['id'], networks_list)

    def test_create_delete_networks(self):
        """Covered test cases:
        * Creating vlan profiles
        * Deleting vlan profiles
        * Adding vlans to both VNICs of a service profile
        * Deleting vlans from both VNICs of a service profile
        """
        # Create network and subnet (DHCP enabled)
        network = self._create_network()
        self.assertEqual('ACTIVE', network['status'])
        self._create_subnet(network)
        port = self._create_port(
            network.id, security_groups=[self.security_group['id']])

        # Get a vlan id and verify a vlan profile has been created
        network = self.admin_networks_client.show_network(network['id'])['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify vlan has been added to both vnics
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: self.ucsm.get_ether_vlan(self.network_node_profile,
                                                 eth_name, vlan_id))

        # Delete network and verify that the vlan profile has been removed
        port.delete()
        self._delete_network(network)
        self.timed_assert(self.assertEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify the vlan has been removed from both vnics
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertEmpty,
                lambda: self.ucsm.get_ether_vlan(
                    self.network_node_profile, eth_name, vlan_id))
