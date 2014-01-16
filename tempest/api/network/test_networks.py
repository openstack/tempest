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

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.test import attr

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
        port create
        port delete
        port list
        port show
        port update
        network update
        subnet update

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
    def setUpClass(cls):
        super(NetworksTestJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.name = cls.network['name']
        cls.subnet = cls.create_subnet(cls.network)
        cls.cidr = cls.subnet['cidr']
        cls.port = cls.create_port(cls.network)

    @attr(type='smoke')
    def test_create_update_delete_network_subnet(self):
        # Creates a network
        name = data_utils.rand_name('network-')
        resp, body = self.client.create_network(name=name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        net_id = network['id']
        # Verification of network update
        new_name = "New_network"
        resp, body = self.client.update_network(net_id, name=new_name)
        self.assertEqual('200', resp['status'])
        updated_net = body['network']
        self.assertEqual(updated_net['name'], new_name)
        # Find a cidr that is not in use yet and create a subnet with it
        cidr = netaddr.IPNetwork(self._tenant_network_cidr)
        mask_bits = self._tenant_network_mask_bits
        for subnet_cidr in cidr.subnet(mask_bits):
            try:
                resp, body = self.client.create_subnet(
                    network_id=net_id,
                    cidr=str(subnet_cidr),
                    ip_version=self._ip_version)
                break
            except exceptions.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertEqual('201', resp['status'])
        subnet = body['subnet']
        subnet_id = subnet['id']
        # Verification of subnet update
        new_subnet = "New_subnet"
        resp, body = self.client.update_subnet(subnet_id,
                                               name=new_subnet)
        self.assertEqual('200', resp['status'])
        updated_subnet = body['subnet']
        self.assertEqual(updated_subnet['name'], new_subnet)
        # Delete subnet and network
        resp, body = self.client.delete_subnet(subnet_id)
        self.assertEqual('204', resp['status'])
        resp, body = self.client.delete_network(net_id)
        self.assertEqual('204', resp['status'])

    @attr(type='smoke')
    def test_show_network(self):
        # Verifies the details of a network
        resp, body = self.client.show_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(self.network['id'], network['id'])
        self.assertEqual(self.name, network['name'])

    @attr(type='smoke')
    def test_list_networks(self):
        # Verify the network exists in the list of all networks
        resp, body = self.client.list_networks()
        self.assertEqual('200', resp['status'])
        networks = body['networks']
        found = None
        for n in networks:
            if (n['id'] == self.network['id']):
                found = n['id']
        msg = "Network list doesn't contain created network"
        self.assertIsNotNone(found, msg)

    @attr(type='smoke')
    def test_list_networks_fields(self):
        # Verify listing some fields of the networks
        resp, body = self.client.list_networks(fields='id')
        self.assertEqual('200', resp['status'])
        networks = body['networks']
        found = None
        for n in networks:
            self.assertEqual(len(n), 1)
            self.assertIn('id', n)
            if (n['id'] == self.network['id']):
                found = n['id']
        self.assertIsNotNone(found,
                             "Created network id not found in the list")

    @attr(type='smoke')
    def test_show_subnet(self):
        # Verifies the details of a subnet
        resp, body = self.client.show_subnet(self.subnet['id'])
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertEqual(self.subnet['id'], subnet['id'])
        self.assertEqual(self.cidr, subnet['cidr'])

    @attr(type='smoke')
    def test_list_subnets(self):
        # Verify the subnet exists in the list of all subnets
        resp, body = self.client.list_subnets()
        self.assertEqual('200', resp['status'])
        subnets = body['subnets']
        found = None
        for n in subnets:
            if (n['id'] == self.subnet['id']):
                found = n['id']
        msg = "Subnet list doesn't contain created subnet"
        self.assertIsNotNone(found, msg)

    @attr(type='smoke')
    def test_list_subnets_fields(self):
        # Verify listing some fields of the subnets
        resp, body = self.client.list_subnets(fields='id')
        self.assertEqual('200', resp['status'])
        subnets = body['subnets']
        found = None
        for n in subnets:
            self.assertEqual(len(n), 1)
            self.assertIn('id', n)
            if (n['id'] == self.subnet['id']):
                found = n['id']
        self.assertIsNotNone(found,
                             "Created subnet id not found in the list")

    @attr(type='smoke')
    def test_create_update_delete_port(self):
        # Verify that successful port creation, update & deletion
        resp, body = self.client.create_port(
            network_id=self.network['id'])
        self.assertEqual('201', resp['status'])
        port = body['port']
        # Verification of port update
        new_port = "New_Port"
        resp, body = self.client.update_port(port['id'], name=new_port)
        self.assertEqual('200', resp['status'])
        updated_port = body['port']
        self.assertEqual(updated_port['name'], new_port)
        # Verification of port delete
        resp, body = self.client.delete_port(port['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='smoke')
    def test_show_port(self):
        # Verify the details of port
        resp, body = self.client.show_port(self.port['id'])
        self.assertEqual('200', resp['status'])
        port = body['port']
        self.assertEqual(self.port['id'], port['id'])

    @attr(type='smoke')
    def test_list_ports(self):
        # Verify the port exists in the list of all ports
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports_list = body['ports']
        found = None
        for n in ports_list:
            if (n['id'] == self.port['id']):
                found = n['id']
        self.assertIsNotNone(found, "Port list doesn't contain created port")

    @attr(type='smoke')
    def test_list_ports_fields(self):
        # Verify listing some fields of the ports
        resp, body = self.client.list_ports(fields='id')
        self.assertEqual('200', resp['status'])
        ports_list = body['ports']
        found = None
        for n in ports_list:
            self.assertEqual(len(n), 1)
            self.assertIn('id', n)
            if (n['id'] == self.port['id']):
                found = n['id']
        self.assertIsNotNone(found,
                             "Created port id not found in the list")


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

    @classmethod
    def setUpClass(cls):
        super(BulkNetworkOpsTestJSON, cls).setUpClass()
        cls.network1 = cls.create_network()
        cls.network2 = cls.create_network()

    def _delete_networks(self, created_networks):
        for n in created_networks:
            resp, body = self.client.delete_network(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the networks are not found in the list after deletion
        resp, body = self.client.list_networks()
        networks_list = list()
        for network in body['networks']:
            networks_list.append(network['id'])
        for n in created_networks:
            self.assertNotIn(n['id'], networks_list)

    def _delete_subnets(self, created_subnets):
        for n in created_subnets:
            resp, body = self.client.delete_subnet(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the subnets are not found in the list after deletion
        resp, body = self.client.list_subnets()
        subnets_list = list()
        for subnet in body['subnets']:
            subnets_list.append(subnet['id'])
        for n in created_subnets:
            self.assertNotIn(n['id'], subnets_list)

    def _delete_ports(self, created_ports):
        for n in created_ports:
            resp, body = self.client.delete_port(n['id'])
            self.assertEqual(204, resp.status)
        # Asserting that the ports are not found in the list after deletion
        resp, body = self.client.list_ports()
        ports_list = list()
        for port in body['ports']:
            ports_list.append(port['id'])
        for n in created_ports:
            self.assertNotIn(n['id'], ports_list)

    @attr(type='smoke')
    def test_bulk_create_delete_network(self):
        # Creates 2 networks in one request
        network_names = [data_utils.rand_name('network-'),
                         data_utils.rand_name('network-')]
        resp, body = self.client.create_bulk_network(2, network_names)
        created_networks = body['networks']
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_networks, created_networks)
        # Asserting that the networks are found in the list after creation
        resp, body = self.client.list_networks()
        networks_list = list()
        for network in body['networks']:
            networks_list.append(network['id'])
        for n in created_networks:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], networks_list)

    @attr(type='smoke')
    def test_bulk_create_delete_subnet(self):
        # Creates 2 subnets in one request
        cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cidrs = []
        for subnet_cidr in cidr.subnet(mask_bits):
            cidrs.append(subnet_cidr)
        names = []
        networks = [self.network1['id'], self.network2['id']]
        for i in range(len(networks)):
            names.append(data_utils.rand_name('subnet-'))
        subnet_list = []
        # TODO(raies): "for IPv6, version list [4, 6] will be used.
        # and cidr for IPv6 will be of IPv6"
        ip_version = [4, 4]
        for i in range(len(names)):
            p1 = {
                'network_id': networks[i],
                'cidr': str(cidrs[(i)]),
                'name': names[i],
                'ip_version': ip_version[i]
            }
            subnet_list.append(p1)
        del subnet_list[1]['name']
        resp, body = self.client.create_bulk_subnet(subnet_list)
        created_subnets = body['subnets']
        self.addCleanup(self._delete_subnets, created_subnets)
        self.assertEqual('201', resp['status'])
        # Asserting that the subnets are found in the list after creation
        resp, body = self.client.list_subnets()
        subnets_list = list()
        for subnet in body['subnets']:
            subnets_list.append(subnet['id'])
        for n in created_subnets:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], subnets_list)

    @attr(type='smoke')
    def test_bulk_create_delete_port(self):
        # Creates 2 ports in one request
        names = []
        networks = [self.network1['id'], self.network2['id']]
        for i in range(len(networks)):
            names.append(data_utils.rand_name('port-'))
        port_list = []
        state = [True, False]
        for i in range(len(names)):
            p1 = {
                'network_id': networks[i],
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
        ports_list = list()
        for port in body['ports']:
            ports_list.append(port['id'])
        for n in created_ports:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], ports_list)


class BulkNetworkOpsTestXML(BulkNetworkOpsTestJSON):
    _interface = 'xml'


class NetworksIpV6TestJSON(NetworksTestJSON):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr
    _tenant_network_mask_bits = CONF.network.tenant_network_v6_mask_bits


class NetworksIpV6TestXML(NetworksIpV6TestJSON):
    _interface = 'xml'
