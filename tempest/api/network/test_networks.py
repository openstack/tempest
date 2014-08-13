# Copyright 2012 OpenStack Foundation
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

import netaddr
import testtools

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class NetworksTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        create a network for a tenant
        list tenant's networks
        show a tenant network details
        create a subnet for a tenant
        list tenant's subnets
        show a tenant subnet details
        network update
        subnet update
        delete a network also deletes its subnets

        All subnet tests are run once with ipv4 and once with ipv6.

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        tenant_network_cidr with a block of cidr's from which smaller blocks
        can be allocated for tenant ipv4 subnets

        tenant_network_v6_cidr is the equivalent for ipv6 subnets

        tenant_network_mask_bits with the mask bits to be used to partition the
        block defined by tenant_network_cidr

        tenant_network_v6_mask_bits is the equivalent for ipv6 subnets
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(NetworksTestJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.name = cls.network['name']
        cls.subnet = cls.create_subnet(cls.network)
        cls.cidr = cls.subnet['cidr']

    @test.attr(type='smoke')
    def test_create_update_delete_network_subnet(self):
        # Create a network
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        # Verify network update
        new_name = "New_network"
        resp, body = self.client.update_network(net_id, name=new_name)
        self.assertEqual('200', resp['status'])
        updated_net = body['network']
        self.assertEqual(updated_net['name'], new_name)
        # Find a cidr that is not in use yet and create a subnet with it
        subnet = self.create_subnet(network)
        subnet_id = subnet['id']
        # Verify subnet update
        new_name = "New_subnet"
        resp, body = self.client.update_subnet(subnet_id, name=new_name)
        self.assertEqual('200', resp['status'])
        updated_subnet = body['subnet']
        self.assertEqual(updated_subnet['name'], new_name)
        # Delete subnet and network
        resp, body = self.client.delete_subnet(subnet_id)
        self.assertEqual('204', resp['status'])
        # Remove subnet from cleanup list
        self.subnets.pop()
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_show_network(self):
        # Verify the details of a network
        resp, body = self.client.show_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        for key in ['id', 'name']:
            self.assertEqual(network[key], self.network[key])

    @test.attr(type='smoke')
    def test_show_network_fields(self):
        # Verify specific fields of a network
        fields = ['id', 'name']
        resp, body = self.client.show_network(self.network['id'],
                                              fields=fields)
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(sorted(network.keys()), sorted(fields))
        for field_name in fields:
            self.assertEqual(network[field_name], self.network[field_name])

    @test.attr(type='smoke')
    def test_list_networks(self):
        # Verify the network exists in the list of all networks
        resp, body = self.client.list_networks()
        self.assertEqual('200', resp['status'])
        networks = [network['id'] for network in body['networks']
                    if network['id'] == self.network['id']]
        self.assertNotEmpty(networks, "Created network not found in the list")

    @test.attr(type='smoke')
    def test_list_networks_fields(self):
        # Verify specific fields of the networks
        fields = ['id', 'name']
        resp, body = self.client.list_networks(fields=fields)
        self.assertEqual('200', resp['status'])
        networks = body['networks']
        self.assertNotEmpty(networks, "Network list returned is empty")
        for network in networks:
            self.assertEqual(sorted(network.keys()), sorted(fields))

    @test.attr(type='smoke')
    def test_show_subnet(self):
        # Verify the details of a subnet
        resp, body = self.client.show_subnet(self.subnet['id'])
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertNotEmpty(subnet, "Subnet returned has no fields")
        for key in ['id', 'cidr']:
            self.assertIn(key, subnet)
            self.assertEqual(subnet[key], self.subnet[key])

    @test.attr(type='smoke')
    def test_show_subnet_fields(self):
        # Verify specific fields of a subnet
        fields = ['id', 'network_id']
        resp, body = self.client.show_subnet(self.subnet['id'],
                                             fields=fields)
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertEqual(sorted(subnet.keys()), sorted(fields))
        for field_name in fields:
            self.assertEqual(subnet[field_name], self.subnet[field_name])

    @test.attr(type='smoke')
    def test_list_subnets(self):
        # Verify the subnet exists in the list of all subnets
        resp, body = self.client.list_subnets()
        self.assertEqual('200', resp['status'])
        subnets = [subnet['id'] for subnet in body['subnets']
                   if subnet['id'] == self.subnet['id']]
        self.assertNotEmpty(subnets, "Created subnet not found in the list")

    @test.attr(type='smoke')
    def test_list_subnets_fields(self):
        # Verify specific fields of subnets
        fields = ['id', 'network_id']
        resp, body = self.client.list_subnets(fields=fields)
        self.assertEqual('200', resp['status'])
        subnets = body['subnets']
        self.assertNotEmpty(subnets, "Subnet list returned is empty")
        for subnet in subnets:
            self.assertEqual(sorted(subnet.keys()), sorted(fields))

    def _try_delete_network(self, net_id):
        # delete network, if it exists
        try:
            self.client.delete_network(net_id)
        # if network is not found, this means it was deleted in the test
        except exceptions.NotFound:
            pass

    @test.attr(type='smoke')
    def test_delete_network_with_subnet(self):
        # Creates a network
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        self.addCleanup(self._try_delete_network, net_id)

        # Find a cidr that is not in use yet and create a subnet with it
        subnet = self.create_subnet(network)
        subnet_id = subnet['id']

        # Delete network while the subnet still exists
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])

        # Verify that the subnet got automatically deleted.
        self.assertRaises(exceptions.NotFound, self.client.show_subnet,
                          subnet_id)

        # Since create_subnet adds the subnet to the delete list, and it is
        # is actually deleted here - this will create and issue, hence remove
        # it from the list.
        self.subnets.pop()

    @test.attr(type='smoke')
    def test_create_delete_subnet_with_gw(self):
        gateway = '10.100.0.13'
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        subnet = self.create_subnet(network, gateway)
        # Verifies Subnet GW in IPv4
        self.assertEqual(subnet['gateway_ip'], gateway)
        # Delete network and subnet
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])
        self.subnets.pop()

    @test.attr(type='smoke')
    def test_create_delete_subnet_without_gw(self):
        net = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        gateway_ip = str(netaddr.IPAddress(net.first + 1))
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        subnet = self.create_subnet(network)
        # Verifies Subnet GW in IPv4
        self.assertEqual(subnet['gateway_ip'], gateway_ip)
        # Delete network and subnet
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])
        self.subnets.pop()


class NetworksTestXML(NetworksTestJSON):
    _interface = 'xml'


class BulkNetworkOpsTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        bulk network creation
        bulk subnet creation
        bulk port creation
        list tenant's networks

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        tenant_network_cidr with a block of cidr's from which smaller blocks
        can be allocated for tenant networks

        tenant_network_mask_bits with the mask bits to be used to partition the
        block defined by tenant-network_cidr
    """

    def _delete_networks(self, created_networks):
        for n in created_networks:
            resp, body = self.client.delete_network(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the networks are not found in the list after deletion
        resp, body = self.client.list_networks()
        networks_list = [network['id'] for network in body['networks']]
        for n in created_networks:
            self.assertNotIn(n['id'], networks_list)

    def _delete_subnets(self, created_subnets):
        for n in created_subnets:
            resp, body = self.client.delete_subnet(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the subnets are not found in the list after deletion
        resp, body = self.client.list_subnets()
        subnets_list = [subnet['id'] for subnet in body['subnets']]
        for n in created_subnets:
            self.assertNotIn(n['id'], subnets_list)

    def _delete_ports(self, created_ports):
        for n in created_ports:
            resp, body = self.client.delete_port(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the ports are not found in the list after deletion
        resp, body = self.client.list_ports()
        ports_list = [port['id'] for port in body['ports']]
        for n in created_ports:
            self.assertNotIn(n['id'], ports_list)

    @test.attr(type='smoke')
    def test_bulk_create_delete_network(self):
        # Creates 2 networks in one request
        network_names = [data_utils.rand_name('network-'),
                         data_utils.rand_name('network-')]
        resp, body = self.client.create_bulk_network(network_names)
        created_networks = body['networks']
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_networks, created_networks)
        # Asserting that the networks are found in the list after creation
        resp, body = self.client.list_networks()
        networks_list = [network['id'] for network in body['networks']]
        for n in created_networks:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], networks_list)

    @test.attr(type='smoke')
    def test_bulk_create_delete_subnet(self):
        networks = [self.create_network(), self.create_network()]
        # Creates 2 subnets in one request
        cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cidrs = [subnet_cidr for subnet_cidr in cidr.subnet(mask_bits)]
        names = [data_utils.rand_name('subnet-') for i in range(len(networks))]
        subnets_list = []
        # TODO(raies): "for IPv6, version list [4, 6] will be used.
        # and cidr for IPv6 will be of IPv6"
        ip_version = [4, 4]
        for i in range(len(names)):
            p1 = {
                'network_id': networks[i]['id'],
                'cidr': str(cidrs[(i)]),
                'name': names[i],
                'ip_version': ip_version[i]
            }
            subnets_list.append(p1)
        del subnets_list[1]['name']
        resp, body = self.client.create_bulk_subnet(subnets_list)
        created_subnets = body['subnets']
        self.addCleanup(self._delete_subnets, created_subnets)
        self.assertEqual('201', resp['status'])
        # Asserting that the subnets are found in the list after creation
        resp, body = self.client.list_subnets()
        subnets_list = [subnet['id'] for subnet in body['subnets']]
        for n in created_subnets:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], subnets_list)

    @test.attr(type='smoke')
    def test_bulk_create_delete_port(self):
        networks = [self.create_network(), self.create_network()]
        # Creates 2 ports in one request
        names = [data_utils.rand_name('port-') for i in range(len(networks))]
        port_list = []
        state = [True, False]
        for i in range(len(names)):
            p1 = {
                'network_id': networks[i]['id'],
                'name': names[i],
                'admin_state_up': state[i],
            }
            port_list.append(p1)
        del port_list[1]['name']
        resp, body = self.client.create_bulk_port(port_list)
        created_ports = body['ports']
        self.addCleanup(self._delete_ports, created_ports)
        self.assertEqual('201', resp['status'])
        # Asserting that the ports are found in the list after creation
        resp, body = self.client.list_ports()
        ports_list = [port['id'] for port in body['ports']]
        for n in created_ports:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], ports_list)


class BulkNetworkOpsTestXML(BulkNetworkOpsTestJSON):
    _interface = 'xml'


class NetworksIpV6TestJSON(NetworksTestJSON):
    _ip_version = 6

    @classmethod
    def setUpClass(cls):
        if not CONF.network_feature_enabled.ipv6:
            skip_msg = "IPv6 Tests are disabled."
            raise cls.skipException(skip_msg)
        super(NetworksIpV6TestJSON, cls).setUpClass()

    @test.attr(type='smoke')
    def test_create_delete_subnet_with_gw(self):
        gateway = '2003::2'
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        subnet = self.create_subnet(network, gateway)
        # Verifies Subnet GW in IPv6
        self.assertEqual(subnet['gateway_ip'], gateway)
        # Delete network and subnet
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])
        self.subnets.pop()

    @test.attr(type='smoke')
    def test_create_delete_subnet_without_gw(self):
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        subnet = self.create_subnet(network)
        # Verifies Subnet GW in IPv6
        self.assertEqual(subnet['gateway_ip'], '2003::1')
        # Delete network and subnet
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])
        self.subnets.pop()

    @testtools.skipUnless(CONF.network_feature_enabled.ipv6_subnet_attributes,
                          "IPv6 extended attributes for subnets not "
                          "available")
    @test.attr(type='smoke')
    def test_create_delete_subnet_with_v6_attributes(self):
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        subnet = self.create_subnet(network,
                                    gateway='fe80::1',
                                    ipv6_ra_mode='slaac',
                                    ipv6_address_mode='slaac')
        # Verifies Subnet GW in IPv6
        self.assertEqual(subnet['gateway_ip'], 'fe80::1')
        self.assertEqual(subnet['ipv6_ra_mode'], 'slaac')
        self.assertEqual(subnet['ipv6_address_mode'], 'slaac')
        # Delete network and subnet
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])
        self.subnets.pop()


class NetworksIpV6TestXML(NetworksIpV6TestJSON):
    _interface = 'xml'
