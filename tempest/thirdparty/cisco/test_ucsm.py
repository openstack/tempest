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
debug = true
use_stderr = false
log_file = tempest.log

[auth]
tempest_roles = _member_
allow_tenant_isolation = True

[compute]
ssh_auth_method = 'configured'
# username to log into an instance.
image_ssh_user = 'root'
# password to log into an instance
image_ssh_password = 'ubuntu'
# flavor id. The flavor should have >= 4Gb of RAM
flavor_ref = 3
flavor_ref_alt = 3
# Image id. Used to boot an instance
image_ref = 60ad4b1e-c5d4-49ad-a9ca-6374c1d8b3f6
# Same as above
image_ref_alt = 60ad4b1e-c5d4-49ad-a9ca-6374c1d8b3f6

[identity]
username = demo
tenant_name = demo
password = demo
alt_username = alt_demo
alt_tenant_name = alt_demo
alt_password = secrete
# There should be OS admin user (with admin role) credentials.
# It will be used by the tests to create another non-admin users
admin_username = admin
admin_tenant_name = admin
admin_domain_name = Default
disable_ssl_certificate_validation = false
# Set correct IP address
uri = http://172.29.173.85:5000/v2.0/
auth_version = v2
# Set correct admin password
admin_password = 1567c9ff7c66376a333d28dfa1a5a3cd717156c7
# Set correct IP address
uri_v3 = http://172.29.173.85:5000/v3/
# Set correct admin tenant id
admin_tenant_id = 725d6fa98000418f88e47d283d8f1efb

[service_available]
neutron = True

[network]
# id of your public network
public_network_id = 1c87c1d3-bd1a-4738-bd55-99a84fa45c87

[ucsm]
# UCSM VIP
ucsm_ip=10.30.119.66
# UCSM username
ucsm_username=admin
# UCSM ppassword
ucsm_password=cisco
# Dictionary of <hostname> VS <UCSM service profile name>
ucsm_host_dict=overcloud-controller-0.localdomain:QA2,overcloud-compute-0.localdomain:QA3,overcloud-compute-1.localdomain:QA4
network_node_list=overcloud-controller-0.localdomain, overcloud-controller-1.localdomain  # list of hostnames of a network nodes
eth_names=eth0,eth1
# Amount of "SR-IOV ports"/"Dynamic VNICs"/"Virtual functions"
virtual_functions_amount=4


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

import netaddr
import random
import testtools
import time

from oslo_log import log
from tempest_lib.common.utils import data_utils

from tempest.common import waiters
from tempest import config
from tempest.scenario import manager
from tempest import test
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

        self.keypairs = {}
        self.servers = []
        self.security_group = \
            self._create_security_group(tenant_id=self.tenant_id)

        # Log into UCS Manager
        self.ucsm_setup()
        self.addCleanup(self.ucsm_cleanup)

    def _get_server_key(self, server):
        return self.keypairs[server['key_name']]['private_key']

    def _create_server(self, name, network_id=None,
                       port_id=None, availability_zone=None):
        keypair = self.create_keypair()
        self.keypairs[keypair['name']] = keypair
        security_groups = [{'name': self.security_group['name']}]
        create_kwargs = {
            'networks': [{}],
            'key_name': keypair['name'],
            'security_groups': security_groups,
        }
        if network_id is not None:
            create_kwargs['networks'][0]['uuid'] = network_id
        if port_id is not None:
            create_kwargs['networks'][0]['port'] = port_id
        if availability_zone is not None:
            create_kwargs['availability_zone'] = availability_zone
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        self.servers.append(server)
        return server

    def check_public_network_connectivity(
            self, server, floating_ip, should_connect=True, msg=None,
            should_check_floating_ip_status=True):
        """Verifies connectivty to a VM via public network and floating IP,
        and verifies floating IP has resource status is correct.
        """
        ssh_login = CONF.compute.image_ssh_user
        ip_address = floating_ip.floating_ip_address
        private_key = None
        floatingip_status = 'DOWN'
        if should_connect:
            private_key = self._get_server_key(server)
            floatingip_status = 'ACTIVE'
        # Check FloatingIP Status before initiating a connection
        if should_check_floating_ip_status:
            self.check_floating_ip_status(floating_ip, floatingip_status)
        # call the common method in the parent class
        super(UCSMTest, self).check_public_network_connectivity(
            ip_address, ssh_login, private_key, should_connect, msg,
            self.servers)

    def assert_vm_to_vm_connectivity(self, server1, server2):
        floating_ip1 = self.create_floating_ip(server1)
        floating_ip2 = self.create_floating_ip(server2)

        # Wait while driver applies settings
        time.sleep(10)
        server1_client = self.get_remote_client(
            floating_ip1.floating_ip_address,
            CONF.compute.image_ssh_user,
            self._get_server_key(server1))
        server2_client = self.get_remote_client(
            floating_ip2.floating_ip_address,
            CONF.compute.image_ssh_user,
            self._get_server_key(server2))
        # Ping server2 from server1 and vice versa
        self.assertNotEmpty(
            server1_client.ping_host(floating_ip2.floating_ip_address))
        self.assertNotEmpty(
            server2_client.ping_host(floating_ip1.floating_ip_address))

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

    @test.attr(type='non-sriov')
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

    @test.attr(type='non-sriov')
    def test_create_delete_bulk_networks(self):
        """Covered test cases:
        * Create bulk vlan profiles
        * Add bulk vlans to both vnics
        * Delete bulk vlans from both vnics
        """
        # Create networks
        names = [data_utils.rand_name('network-') for i in range(5)]
        networks = self.network_client.create_bulk_network(names)['networks']

        # Create subnets (DHCP enabled)
        cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cidrs = [subnet_cidr for subnet_cidr in cidr.subnet(mask_bits)]
        names = [data_utils.rand_name('subnet-')
                 for i in range(len(networks))]
        subnets_list = []
        for i in range(len(names)):
            p1 = {
                'network_id': networks[i]['id'],
                'cidr': str(cidrs[(i)]),
                'name': names[i],
                'ip_version': 4
            }
            subnets_list.append(p1)
        self.network_client.create_bulk_subnet(subnets_list)

        ports_list = []
        for network in networks:
            ports_list.append(self._create_port(
                network['id'], security_groups=[self.security_group['id']]))

        # Get vlan ids and verify vlan profiles have been created
        vlan_ids = [self.admin_networks_client.show_network(n['id'])
                    ['network']['provider:segmentation_id'] for n in networks]
        for vlan_id in vlan_ids:
            self.timed_assert(self.assertNotEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))
            # Verify all vlans have been added to both vnics
            for eth_name in self.eth_names:
                self.timed_assert(
                    self.assertNotEmpty,
                    lambda: self.ucsm.get_ether_vlan(
                        self.network_node_profile, eth_name, vlan_id))

        # Delete networks and verify all vlan profiles have been removed
        for port in ports_list:
            port.delete()
        self._delete_networks(networks)
        for vlan_id in vlan_ids:
            self.timed_assert(self.assertEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))
            # Verify all vlans have been removed from both vnics
            for eth_name in self.eth_names:
                self.timed_assert(
                    self.assertEmpty,
                    lambda: self.ucsm.get_ether_vlan(
                        self.network_node_profile, eth_name, vlan_id))

    @testtools.skip("Feature not implemented")
    @test.attr(type='non-sriov')
    def test_create_vlan_profile_invalid_vlan_id(self):
        """Covered test cases:
        * Driver does not create VLAN profiles if VLAN ID >= 4000
        """
        segmentation_id = random.randint(4000, 4093)
        kwargs = {'provider:network_type': 'vlan',
                  'provider:physical_network': 'physnet1',
                  'provider:segmentation_id': segmentation_id}
        # TODO(nfedotov): Should raise exception.
        # UCSM does not allow to create vlans
        # from 4000 to 4093 (need to figure out correct values)
        self.admin_networks_client.create_network(
            name=data_utils.rand_name('network-'), **kwargs)['network']

    @test.attr(type='sriov')
    # @testtools.skip("https://bugs.launchpad.net/"
    #                 "networking-cisco/+bug/1476721")
    def test_create_delete_sriov_port(self):
        """Covered test cases:
        * Creating SR-IOV port and port profile
        * Deleting SR-IOV port and port profile
        * Attaching instance to SR-IOV port
        """
        # Create network, subnet and port (type=direct)
        network_obj = self._create_network()
        self.assertEqual('ACTIVE', network_obj['status'])
        self._create_subnet(network_obj, enable_dhcp=False)
        kwargs = {'binding:vnic_type': 'direct'}
        port_obj = self._create_port(network_obj.id, **kwargs)
        create_kwargs = {
            'networks': [
                {'port': port_obj.id},
            ]
        }
        # Create server
        server_name = data_utils.rand_name('server-smoke')
        server = self.create_server(name=server_name,
                                    create_kwargs=create_kwargs)

        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify port profile has been created
        port = self.admin_network_client.show_port(port_obj.id)['port']
        port_profile_id = port['binding:vif_details'].get('profileid', None)
        port_profile_dn = 'fabric/lan/profiles/vnic-' + port_profile_id
        self.assertIsNotNone(port_profile_id,
                             'vif_details have a profileid attribute')
        port_profile = self.ucsm.get_port_profile(port_profile_dn)
        self.assertNotEmpty(port_profile,
                            'Port profile has been created in UCSM')
        # Verify the port profile has a correct VLAN
        port_profile_vlans = self.ucsm.get_vnic_ether_if(port_profile)
        self.assertEqual(str(vlan_id), port_profile_vlans[0].Vnet,
                         'Vlan has been added to port profile')

        # Delete server, port, network. Verify port profile and vlan have
        # been removed
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        port_obj.delete()
        network_obj.delete()
        self.assertEmpty(self.ucsm.get_port_profile(port_profile_dn),
                         'Port profile has been removed in UCSM')
        self.timed_assert(self.assertEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

    @test.attr(type='sriov')
    # @testtools.skip("https://bugs.launchpad.net/"
    #                 "networking-cisco/+bug/1476721")
    def test_create_delete_bulk_sriov_ports(self):
        """Covered test cases:
        * Create bulk port profiles
        * Delete bulk port profiles
        """
        # Create networks
        names = [data_utils.rand_name('network-')
                 for i in range(self.virtual_functions)]
        networks = self.network_client.create_bulk_network(names)['networks']

        # Create subnets
        cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cidrs = [subnet_cidr for subnet_cidr in cidr.subnet(mask_bits)]
        names = [data_utils.rand_name('subnet-') for i in range(len(networks))]
        subnets_list = []
        for i in range(len(names)):
            net = {
                'network_id': networks[i]['id'],
                'cidr': str(cidrs[(i)]),
                'name': names[i],
                'ip_version': 4,
                'enable_dhcp': False
            }
            subnets_list.append(net)
        self.network_client.create_bulk_subnet(subnets_list)

        # Create ports
        ports_data = {}
        for network in networks:
            net_id = network['id']
            vlan_id = self.admin_networks_client.show_network(
                net_id)['network']['provider:segmentation_id']
            port = {
                'network_id': net_id,
                'binding:vnic_type': 'direct'
            }
            ports_data[vlan_id] = port
        ports_list = self.network_client.create_bulk_port(
            ports_data.values())['ports']

        # Boot servers
        ports = {}
        servers = {}
        for port in ports_list:
            create_kwargs = {
                'networks': [
                    {'port': port['id']},
                ]
            }
            server_name = data_utils.rand_name('server-smoke')
            server = self._create_server(
                server_name, port_id=port['id'],
                availability_zone='nova:' + self.master_host)

            # Create ports dictionary
            # Assume we create one port per network.
            # Will identify port by network_id
            for vlan_id, pd in ports_data.iteritems():
                if port['network_id'] == pd['network_id']:
                    ports[vlan_id] = self.admin_network_client.show_port(
                        port['id'])['port']
                    servers[vlan_id] = server
                    break

        # Verify port profiles have been created
        for vlan_id, port in ports.iteritems():
            self.timed_assert(self.assertNotEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))

            # Verify port profile has been created
            port_profile_id = port['binding:vif_details'].get('profileid',
                                                              None)
            port_profile_dn = 'fabric/lan/profiles/vnic-' + port_profile_id
            self.assertIsNotNone(port_profile_id,
                                 'vif_details have a profileid attribute')
            port_profile = self.ucsm.get_port_profile(port_profile_dn)
            self.assertNotEmpty(port_profile,
                                'Port profile has been created in UCSM')
            port_profile_vlans = self.ucsm.get_vnic_ether_if(port_profile)
            self.assertEqual(str(vlan_id), port_profile_vlans[0].Vnet,
                             'Vlan has been added to port profile')

        # Delete servers and ports
        for vlan_id, server in servers.iteritems():
            self.servers_client.delete_server(server['id'])
            waiters.wait_for_server_termination(self.servers_client, server['id'])
            self.network_client.delete_port(ports[vlan_id]['id'])

        # Delete networks
        for network in networks:
            self.networks_client.delete_network(network['id'])

        # Verify all port profiles have been removed
        for vlan_id, port in ports.iteritems():
            port_profile_id = port['binding:vif_details'].get('profileid',
                                                              None)
            port_profile_dn = 'fabric/lan/profiles/vnic-' + port_profile_id
            self.assertEmpty(self.ucsm.get_port_profile(port_profile_dn),
                             'Port profile has been removed in UCSM')
            self.timed_assert(self.assertEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))

    @test.attr(type='sriov')
    def test_sriov_intra_vm_to_vm(self):
        """Covered test cases:
        * Intra VM to VM connectivity
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']],
                  'binding:vnic_type': 'direct'}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + self.master_host)
        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + self.master_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='sriov')
    def test_sriov_inter_vm_to_vm(self):
        """Covered test cases:
        * Inter VM to VM connectivity
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']],
                  'binding:vnic_type': 'direct'}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + self.master_host)
        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + self.slave_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_port_attach(self):
        """Covered test cases:
        * Attach instance to non-SR-IOV port
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        port_obj = self._create_port(
            network_obj.id, security_groups=[self.security_group['id']])
        server = self._create_server(data_utils.rand_name('server-smoke'),
                                     network_obj.id, port_id=port_obj.id)
        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify vlan has been added to a compute where instance is launched
        port = self.admin_network_client.show_port(port_obj.id)['port']
        binding_host_id = port['binding:host_id']
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: self.ucsm.get_ether_vlan(
                    self.ucsm_host_dict[binding_host_id], eth_name, vlan_id))

        floating_ip = self.create_floating_ip(server)
        self.check_public_network_connectivity(server, floating_ip)

    @test.attr(type='non-sriov')
    def test_non_sriov_intra_vm_to_vm(self):
        """Covered test cases:
        * Intra VM to VM connectivity
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + self.master_host)
        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + self.master_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_inter_vm_to_vm(self):
        """Covered test cases:
        * Inter VM to VM connectivity
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + self.master_host)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + self.slave_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_delete_second_instance(self):
        """Covered test cases:
        * The driver does not delete vlan if there is at
        least one instance on a host
        """
        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + self.master_host)
        # Create server #2 on the same host
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + self.master_host)
        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify vlan has been added to a host where instance is launched
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: self.ucsm.get_ether_vlan(
                    self.ucsm_host_dict[self.master_host], eth_name, vlan_id))

        self.servers_client.delete_server(server2['id'])
        waiters.wait_for_server_termination(self.servers_client, server2['id'])
        port_obj2.delete()

        # Sleep some time to let neutron process all events.
        time.sleep(20)

        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify vlan has been added to a host where instance is launched
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: self.ucsm.get_ether_vlan(
                    self.ucsm_host_dict[self.master_host], eth_name, vlan_id))

        floating_ip1 = self.create_floating_ip(server1)
        self.check_public_network_connectivity(server1, floating_ip1)
