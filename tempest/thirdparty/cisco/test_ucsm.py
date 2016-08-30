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

##############################################################################
# Example of tempest.conf file
##############################################################################

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
# Dictionary of <hostname> VS <UCSM service profile name>. Compute nodes
compute_host_dict=controller:org-root/ls-tmpl,compute-1:org-root/ls-tmpl
# Dictionary of <hostname> VS <UCSM service profile name>. Controller nodes
controller_host_dict=controller:org-root/ls-tmpl
# List of vNIC names
eth_names=eth0,eth1
# Amount of "SR-IOV ports"/"Dynamic VNICs"/"Virtual functions"
virtual_functions_amount=4

# Set it to False if you wnat to skip sonnectivity tests
test_connectivity=True

# Parameters needed for testing multi-ucsm installation
# UCSMs list. Each UCSM has it's own section named [ucsm:<ucsm ip>] below
ucsm_list = 10.10.0.200,10.10.0.156

# List of physical networks used in Openstack
physnets = physnet1

# Parameters of a particular UCSM
[ucsm:10.10.0.200]
eth_names=eth0,eth1
ucsm_username=ucspe
ucsm_password=ucspe
# Dictionary of controller nodes and service profiles associated with them
controller_host_dict=controller:org-root/ls-sp11
# Dictionary of compute nodes and service profiles associated with them
compute_host_dict=controller:org-root/ls-sp11
# Dictionary of vNIC templates
vnic_template_dict = physnet1:org-root/lan-conn-templ-vnic_template

[ucsm:10.10.0.156]
eth_names=eth0,eth1
ucsm_username=ucspe
ucsm_password=ucspe
#controller_host_dict=controller
compute_host_dict=compute-1:org-root/ls-sp21
vnic_template_dict = physnet1:org-root/lan-conn-templ-vnic_template

##############################################################################
#
##############################################################################


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
from tempest.lib.common.utils import data_utils

from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.scenario import manager
#from tempest.services.network import resources as net_resources
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
        cls.manager = cls.os_adm
        super(UCSMTest, cls).setup_clients()
        # TODO: remove lines below
        cls.admin_networks_client = cls.os_adm.networks_client
        cls.admin_ports_client = cls.os_adm.ports_client
        cls.admin_hosts_client = cls.os_adm.hosts_client
        cls.servers_client = cls.os_adm.servers_client

    @classmethod
    def resource_setup(cls):
        super(UCSMTest, cls).resource_setup()
        super(UCSMTest, cls).ucsm_resource_setup()

    def setUp(self):
        super(UCSMTest, self).setUp()

        self.keypairs = {}
        self.servers = []
        self.security_group = self._create_security_group(
            security_group_rules_client=self.security_group_rules_client,
            security_groups_client=self.security_groups_client)

        # Log into UCS Manager
        self.ucsm_setup()
        self.addCleanup(self.ucsm_cleanup)

    def _create_security_group(self, security_group_rules_client=None,
                               tenant_id=None,
                               namestart='secgroup-smoke',
                               security_groups_client=None):
        secgroup = super(UCSMTest, self)._create_security_group(
            security_group_rules_client=security_group_rules_client,
            security_groups_client=security_groups_client)
        # The group should allow all protocols
        rulesets = [
            dict(
                # all tcp
                protocol='tcp',
                port_range_min=1,
                port_range_max=65535,
            ),
            dict(
                # all udp
                protocol='udp',
                port_range_min=1,
                port_range_max=65535,
            ),
        ]
        for ruleset in rulesets:
            for r_direction in ['ingress', 'egress']:
                ruleset['direction'] = r_direction
                self._create_security_group_rule(
                    sec_group_rules_client=security_group_rules_client,
                    security_groups_client=security_groups_client,
                    secgroup=secgroup, **ruleset)
        return secgroup

    def _get_server_key(self, server):
        return self.keypairs[server['key_name']]['private_key']

    def create_networks(self, networks_client=None,
                        tenant_id=None, dns_nameservers=None,
                        network_kwargs=None):
        """Create a network with a subnet connected to a router.

        The baremetal driver is a special case since all nodes are
        on the same shared network.

        :param client: network client to create resources with.
        :param tenant_id: id of tenant to create resources in.
        :param dns_nameservers: list of dns servers to send to subnet.
        :returns: network, subnet, router
        """
        network_kwargs = network_kwargs or {}
        if CONF.baremetal.driver_enabled:
            # NOTE(Shrews): This exception is for environments where tenant
            # credential isolation is available, but network separation is
            # not (the current baremetal case). Likely can be removed when
            # test account mgmt is reworked:
            # https://blueprints.launchpad.net/tempest/+spec/test-accounts
            if not CONF.compute.fixed_network_name:
                m = 'fixed_network_name must be specified in config'
                raise exceptions.InvalidConfiguration(m)
            network = self._get_network_by_name(
                CONF.compute.fixed_network_name)
            router = None
            subnet = None
        else:
            network = self._create_network(**network_kwargs)
            if CONF.ucsm.provider_network_id:
                router = None
                subnet = None
            else:
                router = self._get_router(tenant_id=tenant_id)
                subnet_kwargs = dict(network=network)
                # use explicit check because empty list is a valid option
                if dns_nameservers is not None:
                    subnet_kwargs['dns_nameservers'] = dns_nameservers
                subnet = self._create_subnet(**subnet_kwargs)
                subnet.add_to_router(router.id)
        return network, subnet, router

    def _create_network(self, networks_client=None, routers_client=None,
                        tenant_id=None, namestart='network-smoke-', **kwargs):
        if not networks_client:
            networks_client = self.networks_client
        if not tenant_id:
            tenant_id = networks_client.tenant_id
        if not routers_client:
            routers_client = self.routers_client
        name = data_utils.rand_name(namestart)

        if CONF.ucsm.provider_network_id:
            # Get info because this is provider network
            result = networks_client.show_network(CONF.ucsm.provider_network_id)
        else:
            result = networks_client.create_network(name=name, tenant_id=tenant_id, **kwargs)
        network = net_resources.DeletableNetwork(
            networks_client=networks_client,
            routers_client=routers_client,
            **result['network'])
        if CONF.ucsm.provider_network_id:
            # Mock delete method because this is provider network
            network.name = name
            network.delete = lambda: True
        self.assertEqual(network.name, name)
        self.addCleanup(self.delete_wrapper, network.delete)
        return network

    def _create_port(self, network_id, client=None, namestart='port-quotatest',
                     **kwargs):
        if not client:
            client = self.ports_client
        name = data_utils.rand_name(namestart)
        result = client.create_port(
            name=name,
            network_id=network_id,
            **kwargs)
        self.assertIsNotNone(result, 'Unable to allocate port')
        port = net_resources.DeletablePort(ports_client=client,
                                           **result['port'])
        self.addCleanup(self.delete_wrapper, port.delete)
        return port

    def _create_server(self, name, network_id=None,
                       port_id=None, availability_zone=None):
        keypair = self.create_keypair(client=self.keypairs_client)
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
        server = self.create_server(name=name, wait_until='ACTIVE', clients=self.os_adm, **create_kwargs)
        self.servers.append(server)
        return server

    def create_floating_ip(self, thing, external_network_id=None,
                           port_id=None, client=None):
        """Creates a floating IP and associates to a resource/port using
        Neutron client
        """
        if not external_network_id:
            external_network_id = CONF.network.public_network_id
        if not client:
            client = self.floating_ips_client
        if not port_id:
            port_id, ip4 = self._get_server_port_id_and_ip4(thing)
        else:
            ip4 = None

        if CONF.ucsm.provider_network_id:
            return {
                'floating_ip_address': ip4,
                'fixed_ip_address': ip4
            }

        result = client.create_floatingip(
            floating_network_id=external_network_id,
            port_id=port_id,
            tenant_id=thing['tenant_id'],
            fixed_ip_address=ip4
        )
        floating_ip = net_resources.DeletableFloatingIp(
            client=client,
            **result['floatingip'])
        self.addCleanup(self.delete_wrapper, floating_ip.delete)
        return floating_ip

    def check_public_network_connectivity(
            self, server, floating_ip, should_connect=True, msg=None,
            should_check_floating_ip_status=True):
        """Verifies connectivty to a VM via public network and floating IP,
        and verifies floating IP has resource status is correct.
        """
        ssh_login = CONF.validation.image_ssh_user
        ip_address = floating_ip['floating_ip_address']
        private_key = None
        floatingip_status = 'DOWN'
        if should_connect:
            private_key = self._get_server_key(server)
            floatingip_status = 'ACTIVE'
        # Check FloatingIP Status before initiating a connection
        if not CONF.ucsm.provider_network_id:
            # If this not a 'provider network' deployment
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
            floating_ip1['floating_ip_address'],
            CONF.validation.image_ssh_user,
            self._get_server_key(server1))
        server2_client = self.get_remote_client(
            floating_ip2['floating_ip_address'],
            CONF.validation.image_ssh_user,
            self._get_server_key(server2))
        # Ping server2 from server1 and vice versa
        self.assertNotEmpty(
            server1_client.ping_host(floating_ip2['floating_ip_address']))
        self.assertNotEmpty(
            server2_client.ping_host(floating_ip1['floating_ip_address']))

    def assert_vm2vm(self, server1, server2):
        floating_ip1 = self.create_floating_ip(server1)
        floating_ip2 = self.create_floating_ip(server2)

        # Wait while driver applies settings
        time.sleep(10)
        server1_client = self.get_remote_client(
            floating_ip1['floating_ip_address'],
            CONF.validation.image_ssh_user,
            self._get_server_key(server1))
        server2_client = self.get_remote_client(
            floating_ip2['floating_ip_address'],
            CONF.validation.image_ssh_user,
            self._get_server_key(server2))

        nc = 'nc'
        port = 5000
        message = 'Hi there!'
        # Run listener
        server2_client.exec_command('kill -9 `pidof "nc"` || true')
        server2_client.exec_command('{0} -l -p {1} -s {2} > out.log &'.format(nc, port, floating_ip2['fixed_ip_address']))
        # Send message
        server1_client.exec_command(
            'echo -n "{0}" | {1} -w1 -p {2} {3} {4} || true'.format(message, nc, port, floating_ip2['fixed_ip_address'], port))
        # Read received message
        received = server2_client.exec_command("cat out.log; rm out.log")
        self.assertEqual(message, received, 'Verify received message')

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
        self._verify_single_ucsm_configured()

        # Create network and subnet (DHCP enabled)
        network = self._create_network()
        self.assertEqual('ACTIVE', network['status'])
        self._create_subnet(network)
        port = self._create_port(
            network.id, security_groups=[self.security_group['id']])

        # Get a vlan id and verify a vlan profile has been created
        network = self.admin_networks_client.show_network(network['id'])['network']
        vlan_id = network['provider:segmentation_id']

        # Verify VLAN Profiles have not been created yet because there are no
        # active ports
        self.timed_assert(self.assertEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        server = self._create_server(data_utils.rand_name('server-smoke'),
                                     port_id=port['id'])

        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify vlan has been added to both vnics
        for service_profile in self.controller_host_dict.values():
            for eth_name in self.eth_names:
                self.timed_assert(
                    self.assertNotEmpty,
                    lambda: self.ucsm.get_ether_vlan(service_profile,
                                                     eth_name, vlan_id))

        # Delete network and verify that the vlan profile has been removed
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, ['id'])
        port.delete()
        self._delete_network(network)
        self.timed_assert(self.assertEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify the vlan has been removed from both vnics
        for service_profile in self.controller_host_dict.values():
            for eth_name in self.eth_names:
                self.timed_assert(
                    self.assertEmpty,
                    lambda: self.ucsm.get_ether_vlan(
                        service_profile, eth_name, vlan_id))

    @test.attr(type='non-sriov')
    def test_create_delete_bulk_networks(self):
        """Covered test cases:
        * Create bulk vlan profiles
        * Add bulk vlans to both vnics
        * Delete bulk vlans from both vnics
        """
        self._verify_single_ucsm_configured()

        # Create networks
        names = [data_utils.rand_name('network-') for i in range(5)]
        data = {'networks': [{'name': name} for name in names]}
        networks = self.networks_client.create_bulk_networks(**data)['networks']
        vlan_ids = [self.admin_networks_client.show_network(n['id'])
                    ['network']['provider:segmentation_id'] for n in networks]

        # Create subnets (DHCP enabled)
        cidr = netaddr.IPNetwork(CONF.network.project_network_cidr)
        mask_bits = CONF.network.project_network_mask_bits
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
        self.subnets_client.create_bulk_subnets(**{'subnets': subnets_list})

        # Verify VLAN Profiles have not been created yet because there are no
        # active ports
        for vlan_id in vlan_ids:
            self.timed_assert(self.assertEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))

        ports_list = []
        servers_list = []
        for network in networks:
            port = self._create_port(
                network['id'], security_groups=[self.security_group['id']])
            server = self._create_server(data_utils.rand_name('server-smoke'),
                                         port_id=port['id'])
            ports_list.append(port)
            servers_list.append(server)

        # Get vlan ids and verify vlan profiles have been created
        for vlan_id in vlan_ids:
            self.timed_assert(self.assertNotEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))
            # Verify all vlans have been added to both vnics
            for service_profile in self.controller_host_dict.values():
                for eth_name in self.eth_names:
                    self.timed_assert(
                        self.assertNotEmpty,
                        lambda: self.ucsm.get_ether_vlan(
                            service_profile, eth_name, vlan_id))

        # Delete networks and verify all vlan profiles have been removed
        for server in servers_list:
            self.servers_client.delete_server(server['id'])
            waiters.wait_for_server_termination(self.servers_client, ['id'])
        for port in ports_list:
            port.delete()
        self._delete_networks(networks)
        for vlan_id in vlan_ids:
            self.timed_assert(self.assertEmpty,
                              lambda: self.ucsm.get_vlan_profile(vlan_id))
            # Verify all vlans have been removed from both vnics
            for service_profile in self.controller_host_dict.values():
                for eth_name in self.eth_names:
                    self.timed_assert(
                        self.assertEmpty,
                        lambda: self.ucsm.get_ether_vlan(
                            service_profile, eth_name, vlan_id))

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
        self._verify_single_ucsm_configured()
        self._verify_sriov_configured()

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
                                    **create_kwargs)

        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_vlan_profile(vlan_id))

        # Verify port profile has been created
        port = self.admin_ports_client.show_port(port_obj.id)['port']
        port_profile_id = port['binding:vif_details'].get('profileid', None)
        port_profile_dn = 'fabric/lan/profiles/vnic-' + port_profile_id
        self.assertIsNotNone(port_profile_id,
                             'vif_details have a profileid attribute')
        self.timed_assert(self.assertNotEmpty,
                          lambda: self.ucsm.get_port_profile(port_profile_dn))
        port_profile = self.ucsm.get_port_profile(port_profile_dn)
        self.assertNotEmpty(port_profile,
                            'Port profile has been created in UCSM')
        # Verify the port profile has a correct VLAN
        self.timed_assert(self.assertNotEmpty,
                          lambda:  self.ucsm.get_vnic_ether_if(port_profile))
        port_profile_vlans = self.ucsm.get_vnic_ether_if(port_profile)
        self.assertEqual(str(vlan_id), port_profile_vlans[0].Vnet,
                         'Vlan has been added to port profile')

        # Delete server, port, network. Verify port profile and vlan have
        # been removed
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        port_obj.delete()
        network_obj.delete()
#        self.assertEmpty(self.ucsm.get_port_profile(port_profile_dn),
#                         'Port profile has been removed in UCSM')
#        self.timed_assert(self.assertEmpty,
#                          lambda: self.ucsm.get_vlan_profile(vlan_id))

    @test.attr(type='sriov')
    # @testtools.skip("https://bugs.launchpad.net/"
    #                 "networking-cisco/+bug/1476721")
    def test_create_delete_bulk_sriov_ports(self):
        """Covered test cases:
        * Create bulk port profiles
        * Delete bulk port profiles
        """
        self._verify_single_ucsm_configured()
        self._verify_sriov_configured()

        master_host = random.choice(self.compute_host_dict.keys())

        # Create networks
        names = [data_utils.rand_name('network-')
                 for i in range(self.virtual_functions)]
        data = {'networks': [{'name': name} for name in names]}
        networks = self.networks_client.create_bulk_networks(**data)['networks']

        # Create subnets
        cidr = netaddr.IPNetwork(CONF.network.project_network_cidr)
        mask_bits = CONF.network.project_network_mask_bits
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
        self.subnets_client.create_bulk_subnets(**{'subnets': subnets_list})

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

        ports_list = self.ports_client.create_bulk_ports(
            **{'ports': ports_data.values()})['ports']

        # Boot servers
        ports = {}
        servers = {}
        for port in ports_list:
            server_name = data_utils.rand_name('server-smoke')
            server = self._create_server(
                server_name, port_id=port['id'],
                availability_zone='nova:' + master_host)

            # Create ports dictionary
            # Assume we create one port per network.
            # Will identify port by network_id
            for vlan_id, pd in ports_data.iteritems():
                if port['network_id'] == pd['network_id']:
                    ports[vlan_id] = self.admin_ports_client.show_port(
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
            self.timed_assert(self.assertNotEmpty,
                              lambda: self.ucsm.get_port_profile(port_profile_dn))
            port_profile = self.ucsm.get_port_profile(port_profile_dn)
            self.assertNotEmpty(port_profile,
                                'Port profile has been created in UCSM')
            self.timed_assert(self.assertNotEmpty,
                              lambda:self.ucsm.get_vnic_ether_if(port_profile))
            port_profile_vlans = self.ucsm.get_vnic_ether_if(port_profile)
            self.assertEqual(str(vlan_id), port_profile_vlans[0].Vnet,
                             'Vlan has been added to port profile')

        # Delete servers and ports
        for vlan_id, server in servers.iteritems():
            self.servers_client.delete_server(server['id'])
            waiters.wait_for_server_termination(self.servers_client, server['id'])
            self.ports_client.delete_port(ports[vlan_id]['id'])

        # Delete networks
        for network in networks:
            self.networks_client.delete_network(network['id'])

        # Verify all port profiles have been removed
        # for vlan_id, port in ports.iteritems():
        #     port_profile_id = port['binding:vif_details'].get('profileid',
        #                                                       None)
        #     port_profile_dn = 'fabric/lan/profiles/vnic-' + port_profile_id
        #     self.assertEmpty(self.ucsm.get_port_profile(port_profile_dn),
        #                      'Port profile has been removed in UCSM')
        #     self.timed_assert(self.assertEmpty,
        #                       lambda: self.ucsm.get_vlan_profile(vlan_id))

    @test.attr(type='sriov')
    def test_sriov_intra_vm_to_vm(self):
        """Covered test cases:
        * Intra VM to VM connectivity
        """
        self._verify_connectivity_tests_enabled()
        self._verify_single_ucsm_configured()
        self._verify_sriov_configured()

        master_host = random.choice(self.compute_host_dict.keys())

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']],
                  'binding:vnic_type': 'direct'}

        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + master_host)

        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + master_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='sriov')
    def test_sriov_inter_vm_to_vm(self):
        """Covered test cases:
        * Inter VM to VM connectivity
        """
        self._verify_connectivity_tests_enabled()
        self._verify_single_ucsm_configured()
        self._verify_sriov_configured()
        self._verify_more_than_one_compute_host_exist()

        master_host, slave_host = random.sample(self.compute_host_dict.keys(), 2)

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']],
                  'binding:vnic_type': 'direct'}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + master_host)
        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + slave_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_port_attach(self):
        """Covered test cases:
        * Attach instance to non-SR-IOV port
        """
        self._verify_single_ucsm_configured()

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
        port = self.admin_ports_client.show_port(port_obj.id)['port']
        binding_host_id = port['binding:host_id']
        for eth_name in self.eth_names:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: self.ucsm.get_ether_vlan(
                    self.compute_host_dict[binding_host_id], eth_name, vlan_id))

        floating_ip = self.create_floating_ip(server)
        self.check_public_network_connectivity(server, floating_ip)

    @test.attr(type='non-sriov')
    def test_non_sriov_intra_vm_to_vm(self):
        """Covered test cases:
        * Intra VM to VM connectivity
        """
        self._verify_single_ucsm_configured()
        self._verify_connectivity_tests_enabled()

        master_host = random.choice(self.compute_host_dict.keys())

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + master_host)
        # Create server #2 on the same compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + master_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_inter_vm_to_vm(self):
        """Covered test cases:
        * Inter VM to VM connectivity
        """
        self._verify_single_ucsm_configured()
        self._verify_connectivity_tests_enabled()
        self._verify_more_than_one_compute_host_exist()

        if len(self.compute_host_dict.keys()) < 2:
            raise self.skipException('Not enough amount of compute hosts. Need at least 2. '
                                     'Update tempest.conf')

        master_host, slave_host = random.sample(self.compute_host_dict.keys(), 2)

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + master_host)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + slave_host)

        self.assert_vm_to_vm_connectivity(server1, server2)

    @test.attr(type='non-sriov')
    def test_non_sriov_delete_second_instance(self):
        """Covered test cases:
        * The driver does not delete vlan if there is at
        least one instance on a host
        """
        self._verify_single_ucsm_configured()
        self._verify_connectivity_tests_enabled()

        master_host = random.choice(self.compute_host_dict.keys())

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + master_host)
        # Create server #2 on the same host
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + master_host)
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
                    self.compute_host_dict[master_host], eth_name, vlan_id))

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
                    self.compute_host_dict[master_host], eth_name, vlan_id))

        floating_ip1 = self.create_floating_ip(server1)
        self.check_public_network_connectivity(server1, floating_ip1)

    @test.attr(type=['non-sriov', 'multi-ucsm'])
    def test_multi_create_delete_network(self):
        """Covered test cases:
        * The driver creates vlan profile in a certain UCSM
        """
        self._verify_multi_ucsm_configured()

        # UCSMs to which controllers are connected
        ucsm_clients = list()
        for conf in self.multi_ucsm_conf.values():
            if conf.controller_host_dict:
                ucsm_clients.append(self.multi_ucsm_clients[conf['ucsm_ip']])

        # Create network and subnet (DHCP enabled)
        network = self._create_network()
        self.assertEqual('ACTIVE', network['status'])
        self._create_subnet(network)
        port = self._create_port(
            network.id, security_groups=[self.security_group['id']])

        # Get a vlan id and verify a vlan profile has been created
        network = self.admin_networks_client.show_network(network['id'])['network']
        vlan_id = network['provider:segmentation_id']

        for ucsm_client in ucsm_clients:
            self.timed_assert(self.assertNotEmpty, lambda: ucsm_client.get_vlan_profile(vlan_id))

        # # Verify vlan has been added to both vnics
        # for ucsm_client in ucsm_clients:
        #     conf = self.multi_ucsm_conf[ucsm_client.ip]
        #     for controller_sp in conf['controller_host_dict'].values():
        #         for eth_name in conf['eth_names']:
        #             self.timed_assert(
        #                 self.assertNotEmpty,
        #                 lambda: self.ucsm.get_ether_vlan(controller_sp, eth_name, vlan_id))

        # Delete network and verify that the vlan profile has been removed
        port.delete()
        self._delete_network(network)
        for ucsm_client in ucsm_clients:
            self.timed_assert(self.assertEmpty,
                              lambda: ucsm_client.get_vlan_profile(vlan_id))

        # # Verify the vlan has been removed from both vnics
        # for ucsm_client in ucsm_clients:
        #     conf = self.multi_ucsm_conf[ucsm_client.ip]
        #     for controller_sp in conf['controller_host_dict'].values():
        #         for eth_name in conf['eth_names']:
        #             self.timed_assert(
        #                 self.assertEmpty,
        #                 lambda: self.ucsm.get_ether_vlan(controller_sp, eth_name, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'service-profile-templates'])
    def test_multi_desired_ucsm_vnics_configured(self):
        """Covered test cases:

        Multi-UCSM
        * The driver creates vlan profile in a certain UCSM
        * The driver adds vlan profile to vNIC of a service profile located in a certain UCSM
        * The driver deletes vlan profile to vNIC of a service profile located in a certain UCSM
        * Right vNICs are configured in a certain UCSM

        Service Profile templates
        * UCSM driver adds vlans to a vNIC of Service Profile template
        * UCSM driver deletes vlans from vNIC of a Service Profile template
        * VLAN profile is deleted once network is removed
        """
        self._verify_multi_ucsm_configured()
        self._verify_connectivity_tests_enabled()

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        port_obj = self._create_port(network_obj.id, **kwargs)

        random_ucsm = random.choice(self.multi_ucsm_conf.values())
        random_ucsm_client = self.multi_ucsm_clients[random_ucsm['ucsm_ip']]
        random_compute = random.choice(random_ucsm['compute_host_dict'].keys())
        random_compute_sp = random_ucsm['compute_host_dict'][random_compute]
        server = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj.id,
            availability_zone='nova:' + random_compute)

        # Verify vlan profile has been created
        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: random_ucsm_client.get_vlan_profile(vlan_id))

        # Verify vlan has been added to a compute where instance is launched
        port = self.admin_ports_client.show_port(port_obj.id)['port']
        binding_host_id = port['binding:host_id']
        self.assertEqual(random_compute, binding_host_id, 'binding:host_id same as we want')
        for eth_name in random_ucsm['eth_names']:
            self.timed_assert(
                self.assertNotEmpty,
                lambda: random_ucsm_client.get_ether_vlan(random_compute_sp, eth_name, vlan_id))

        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        port_obj.delete()
        subnet_obj.delete()
        network_obj.delete()
        self.timed_assert(self.assertEmpty,
                          lambda: random_ucsm_client.get_vlan_profile(vlan_id))

        for eth_name in random_ucsm['eth_names']:
            self.timed_assert(
                self.assertEmpty,
                lambda: random_ucsm_client.get_ether_vlan(random_compute_sp, eth_name, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'service-profile-templates'])
    def test_multi_inter_vm_to_vm_computes_attached_to_same_fi(self):
        """Covered test cases:

        Multi-UCSM
        * Inter VM to VM connectivity

        Service Profile templates
        * Inter VM to VM connectivity. Computes attached to the same UCSM
        * Instance is able to get IP address from DHCP service
        * VLAN profile is not deleted if it used by at least one Service Profile template
        * Right vNICs are configured in a certain UCSM
        """
        self._verify_multi_ucsm_configured(need_amount=1)
        self._verify_connectivity_tests_enabled()
        self._verify_more_than_one_compute_host_exist()

        ucsm_conf1 = random.choice(self.multi_ucsm_conf.values())
        ucsm_client1 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        compute1, compute2 = random.sample(ucsm_conf1['compute_host_dict'].keys(), 2)

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + compute1)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + compute2)

        self.assert_vm_to_vm_connectivity(server1, server2)

        # Delete one server and verify VLAN profile still exists
        self.servers_client.delete_server(server1['id'])
        waiters.wait_for_server_termination(self.servers_client, server1['id'])
        port_obj1.delete()

        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))

        # Delete another server, ports, subnet, network.
        # Verify VLAN is removed
        self.servers_client.delete_server(server2['id'])
        waiters.wait_for_server_termination(self.servers_client, server2['id'])
        port_obj2.delete()
        subnet_obj.delete()
        network_obj.delete()
        self.timed_assert(self.assertEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))
        for compute in (compute1, compute2):
            for eth_name in ucsm_conf1['eth_names']:
                compute_sp = ucsm_conf1['compute_host_dict'][compute]
                self.timed_assert(
                    self.assertEmpty,
                    lambda: ucsm_client1.get_ether_vlan(compute_sp, eth_name, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'service-profile-templates'])
    def test_multi_inter_vm_to_vm_computes_attached_to_different_fi(self):
        """Covered test cases:

        Multi-UCSM
        * Inter VM to VM connectivity

        Service Profile templates
        * Inter VM to VM connectivity. Computes attached to different UCSMs
        * Instance is able to get IP address from DHCP service
        * VLAN profile is not deleted if it used by at least one Service Profile template
        * Right vNICs are configured in a certain UCSM
        """
        self._verify_multi_ucsm_configured(need_amount=2)
        self._verify_connectivity_tests_enabled()
        self._verify_more_than_one_compute_host_exist()

        ucsm_conf1, ucsm_conf2 = random.sample(self.multi_ucsm_conf.values(), 2)
        ucsm_client1 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        ucsm_client2 = self.multi_ucsm_clients[ucsm_conf2['ucsm_ip']]
        compute1 = random.choice(ucsm_conf1['compute_host_dict'].keys())
        compute2 = random.choice(ucsm_conf2['compute_host_dict'].keys())

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + compute1)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + compute2)

        self.assert_vm_to_vm_connectivity(server1, server2)

        # Delete one server and verify VLAN profile still exists
        self.servers_client.delete_server(server1['id'])
        waiters.wait_for_server_termination(self.servers_client, server1['id'])
        port_obj1.delete()

        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client2.get_vlan_profile(vlan_id))

        # Delete another server, ports, subnet, network.
        # Verify VLAN is removed
        self.servers_client.delete_server(server2['id'])
        waiters.wait_for_server_termination(self.servers_client, server2['id'])
        port_obj2.delete()
        subnet_obj.delete()
        network_obj.delete()
        self.timed_assert(self.assertEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))
        self.timed_assert(self.assertEmpty,
                          lambda: ucsm_client2.get_vlan_profile(vlan_id))
        for conf, cl, cp in ((ucsm_conf1, ucsm_client1, compute1), (ucsm_conf2, ucsm_client2, compute2)):
            for eth_name in conf['eth_names']:
                compute_sp = conf['compute_host_dict'][cp]
                self.timed_assert(
                    self.assertEmpty,
                    lambda: cl.get_ether_vlan(compute_sp, eth_name, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'service-profile-templates'])
    def test_multi_intra_vm_to_vm(self):
        """Covered test cases:

        Service Profile templates
        * Intra VM to VM connectivity
        * Instance is able to get IP address from DHCP service
        * VLAN is not deleted from a service profile template if it used by at least one neutron port on a compute host
        """
        self._verify_multi_ucsm_configured()
        self._verify_connectivity_tests_enabled()

        ucsm_conf1 = random.choice(self.multi_ucsm_conf.values())
        ucsm_client1 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        compute1 = random.choice(ucsm_conf1['compute_host_dict'].keys())

        network_obj, subnet_obj, router_obj = self.create_networks()
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + compute1)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + compute1)

        self.assert_vm_to_vm_connectivity(server1, server2)

        # Delete one server and verify VLAN profile still exists
        self.servers_client.delete_server(server1['id'])
        waiters.wait_for_server_termination(self.servers_client, server1['id'])
        port_obj1.delete()

        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))

        # Delete another server, ports, subnet, network.
        # Verify VLAN is removed
        self.servers_client.delete_server(server2['id'])
        waiters.wait_for_server_termination(self.servers_client, server2['id'])
        port_obj2.delete()
        subnet_obj.delete()
        network_obj.delete()
        self.timed_assert(self.assertEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))
        for eth_name in ucsm_conf1['eth_names']:
            compute_sp = ucsm_conf1['compute_host_dict'][compute1]
            self.timed_assert(
                self.assertEmpty,
                lambda: ucsm_client1.get_ether_vlan(compute_sp, eth_name, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'vnic-templates'])
    def test_multi_vnic_templates_create_delete_network(self):
        """Covered test cases:
        * UCSM Diriver adds vlans to a vNIC template
        * UCSM Driver deletes vlans from a vNIC template
        """
        self._verify_vnic_templates_configured()

        random_physnet = random.choice(CONF.ucsm.physnets)
        # UCSMs to which computes are connected and vNIC template is associated with "random_physnet"
        ucsm_list = list()
        for conf in self.ucsm_confs_with_vnic_templates:
            if conf.compute_host_dict and random_physnet in conf.vnic_template_dict.keys():
                ucsm_list.append(conf)
        if len(ucsm_list) == 0:
            self.skipException('Computes do not use vNIC templates. Check tempest.conf')

        # Create network as an admin user. Only admin user is allowed to set "provider:physical_network"
        params = {'provider:network_type': 'vlan',
                  'provider:physical_network': random_physnet}
        network_obj = self._create_network(networks_client=self.admin_networks_client, **params)
        self.assertEqual('ACTIVE', network_obj['status'])
        # Create subnet (DHCP enabled)
        subnet_obj = self._create_subnet(network_obj)
        port_obj = self._create_port(
            network_obj.id, security_groups=[self.security_group['id']])

        # Choose random UCSM.
        random_ucsm = random.choice(ucsm_list)
        random_ucsm_client = self.multi_ucsm_clients[random_ucsm['ucsm_ip']]
        random_compute = random.choice(random_ucsm['compute_host_dict'].keys())
        vnic_template = random_ucsm['vnic_template_dict'][random_physnet]

        server = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj.id,
            availability_zone='nova:' + random_compute)

        # Get a vlan id and verify a vlan profile has been created
        network = self.admin_networks_client.show_network(network_obj['id'])['network']
        vlan_id = network['provider:segmentation_id']

        self.timed_assert(self.assertNotEmpty,
                          lambda: random_ucsm_client.get_vlan_profile(vlan_id))

        # Verify VLAN is added to vNIC template
        self.timed_assert(self.assertNotEmpty, lambda: random_ucsm_client.get_vnic_template_vlan(vnic_template, vlan_id))

        # Delete server, port, subnet, network
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        port_obj.delete()
        subnet_obj.delete()
        network_obj.delete()

        # Verify vlan profile has been removed
        self.timed_assert(self.assertEmpty,
                          lambda: random_ucsm_client.get_vlan_profile(vlan_id))

        # Verify VLAN is removed from vNIC template
        self.timed_assert(self.assertEmpty, lambda: random_ucsm_client.get_vnic_template_vlan(vnic_template, vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'vnic-templates'])
    def test_multi_vnic_templates_inter_vm_to_vm(self):
        """Covered test cases:

        vNIC templates
        * Inter VM to VM connectivity
        * Instance is able to get IP address from DHCP service
        * VLAN profile is not deleted if it used by at least one vNIC Template
        """
        self._verify_vnic_templates_configured(need_amount=2)
        self._verify_connectivity_tests_enabled()
        self._verify_more_than_one_compute_host_exist()

        random_physnet = random.choice(CONF.ucsm.physnets)
        ucsm_conf1, ucsm_conf2 = random.sample(self.ucsm_confs_with_vnic_templates, 2)
        ucsm_client1 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        ucsm_client2 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        compute1 = random.choice(ucsm_conf1['compute_host_dict'].keys())
        compute2 = random.choice(ucsm_conf2['compute_host_dict'].keys())

        network_kwargs = {'provider:network_type': 'vlan',
                          'provider:physical_network': random_physnet}
        network_obj, subnet_obj, router_obj = self.create_networks(
            networks_client=self.admin_networks_client, network_kwargs=network_kwargs)
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + compute1)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + compute2)

        self.assert_vm_to_vm_connectivity(server1, server2)

        # Delete one server and verify VLAN profile still exists
        self.servers_client.delete_server(server1['id'])
        waiters.wait_for_server_termination(self.servers_client, server1['id'])
        port_obj1.delete()

        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))

        # Verify VLAN is still assigned to vNIC template on another UCSM
        vnic_template = ucsm_conf1['vnic_template_dict'][random_physnet]
        self.timed_assert(self.assertNotEmpty, lambda: ucsm_client2.get_vnic_template_vlan(vnic_template, vlan_id))
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client2.get_vlan_profile(vlan_id))

    @test.attr(type=['non-sriov', 'multi-ucsm', 'vnic-templates'])
    def test_multi_vnic_templates_intra_vm_to_vm(self):
        """Covered test cases:

        vNIC templates
        * Intra VM to VM connectivity
        * Instance is able to get IP address from DHCP service
        * VLAN is not deleted from vNIC template if it used by at least one neutron port on a compute host
        """
        self._verify_vnic_templates_configured()
        self._verify_connectivity_tests_enabled()

        random_physnet = random.choice(CONF.ucsm.physnets)
        ucsm_conf1 = random.choice(self.ucsm_confs_with_vnic_templates)
        ucsm_client1 = self.multi_ucsm_clients[ucsm_conf1['ucsm_ip']]
        compute1 = random.choice(ucsm_conf1['compute_host_dict'].keys())

        network_kwargs = {'provider:network_type': 'vlan',
                          'provider:physical_network': random_physnet}
        network_obj, subnet_obj, router_obj = self.create_networks(
            networks_client=self.admin_networks_client, network_kwargs=network_kwargs)
        kwargs = {'security_groups': [self.security_group['id']]}
        # Create server #1
        port_obj1 = self._create_port(network_obj.id, **kwargs)
        server1 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj1.id,
            availability_zone='nova:' + compute1)
        # Create server #2 on another compute
        port_obj2 = self._create_port(network_obj.id, **kwargs)
        server2 = self._create_server(
            data_utils.rand_name('server-smoke'),
            network_obj.id, port_id=port_obj2.id,
            availability_zone='nova:' + compute1)

        self.assert_vm_to_vm_connectivity(server1, server2)

        # Delete one server and verify VLAN profile still exists
        self.servers_client.delete_server(server1['id'])
        waiters.wait_for_server_termination(self.servers_client, server1['id'])
        port_obj1.delete()

        network = self.admin_networks_client.show_network(
            network_obj.id)['network']
        vlan_id = network['provider:segmentation_id']
        self.timed_assert(self.assertNotEmpty,
                          lambda: ucsm_client1.get_vlan_profile(vlan_id))

        # Verify VLAN is still assigned to vNIC template
        vnic_template = ucsm_conf1['vnic_template_dict'][random_physnet]
        self.timed_assert(self.assertNotEmpty, lambda: ucsm_client1.get_vnic_template_vlan(vnic_template, vlan_id))
