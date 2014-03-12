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

    @attr(type='smoke')
    def test_show_network(self):
        # Verify the details of a network
        resp, body = self.client.show_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        for key in ['id', 'name']:
            self.assertEqual(network[key], self.network[key])

    @attr(type='smoke')
    def test_show_network_fields(self):
        # Verify specific fields of a network
        field_list = [('fields', 'id'), ('fields', 'name'), ]
        resp, body = self.client.show_network(self.network['id'],
                                              field_list=field_list)
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(len(network), len(field_list))
        for label, field_name in field_list:
            self.assertEqual(network[field_name], self.network[field_name])

    @attr(type='smoke')
    def test_list_networks(self):
        # Verify the network exists in the list of all networks
        resp, body = self.client.list_networks()
        self.assertEqual('200', resp['status'])
        networks = [network['id'] for network in body['networks']
                    if network['id'] == self.network['id']]
        self.assertNotEmpty(networks, "Created network not found in the list")

    @attr(type='smoke')
    def test_list_networks_fields(self):
        # Verify specific fields of the networks
        resp, body = self.client.list_networks(fields='id')
        self.assertEqual('200', resp['status'])
        networks = body['networks']
        self.assertNotEmpty(networks, "Network list returned is empty")
        for network in networks:
            self.assertEqual(len(network), 1)
            self.assertIn('id', network)

    @attr(type='smoke')
    def test_show_subnet(self):
        # Verify the details of a subnet
        resp, body = self.client.show_subnet(self.subnet['id'])
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertNotEmpty(subnet, "Subnet returned has no fields")
        for key in ['id', 'cidr']:
            self.assertIn(key, subnet)
            self.assertEqual(subnet[key], self.subnet[key])

    @attr(type='smoke')
    def test_show_subnet_fields(self):
        # Verify specific fields of a subnet
        field_list = [('fields', 'id'), ('fields', 'cidr'), ]
        resp, body = self.client.show_subnet(self.subnet['id'],
                                             field_list=field_list)
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertEqual(len(subnet), len(field_list))
        for label, field_name in field_list:
            self.assertEqual(subnet[field_name], self.subnet[field_name])

    @attr(type='smoke')
    def test_list_subnets(self):
        # Verify the subnet exists in the list of all subnets
        resp, body = self.client.list_subnets()
        self.assertEqual('200', resp['status'])
        subnets = [subnet['id'] for subnet in body['subnets']
                   if subnet['id'] == self.subnet['id']]
        self.assertNotEmpty(subnets, "Created subnet not found in the list")

    @attr(type='smoke')
    def test_list_subnets_fields(self):
        # Verify specific fields of subnets
        resp, body = self.client.list_subnets(fields='id')
        self.assertEqual('200', resp['status'])
        subnets = body['subnets']
        self.assertNotEmpty(subnets, "Subnet list returned is empty")
        for subnet in subnets:
            self.assertEqual(len(subnet), 1)
            self.assertIn('id', subnet)

    @attr(type='smoke')
    def test_create_update_delete_port(self):
        # Verify port creation
        resp, body = self.client.create_port(network_id=self.network['id'])
        self.assertEqual('201', resp['status'])
        port = body['port']
        self.assertTrue(port['admin_state_up'])
        # Verify port update
        new_name = "New_Port"
        resp, body = self.client.update_port(
            port['id'],
            name=new_name,
            admin_state_up=False)
        self.assertEqual('200', resp['status'])
        updated_port = body['port']
        self.assertEqual(updated_port['name'], new_name)
        self.assertFalse(updated_port['admin_state_up'])
        # Verify port deletion
        resp, body = self.client.delete_port(port['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='smoke')
    def test_show_port(self):
        # Verify the details of port
        resp, body = self.client.show_port(self.port['id'])
        self.assertEqual('200', resp['status'])
        port = body['port']
        self.assertIn('id', port)
        self.assertEqual(port['id'], self.port['id'])

    @attr(type='smoke')
    def test_show_port_fields(self):
        # Verify specific fields of a port
        field_list = [('fields', 'id'), ]
        resp, body = self.client.show_port(self.port['id'],
                                           field_list=field_list)
        self.assertEqual('200', resp['status'])
        port = body['port']
        self.assertEqual(len(port), len(field_list))
        for label, field_name in field_list:
            self.assertEqual(port[field_name], self.port[field_name])

    @attr(type='smoke')
    def test_list_ports(self):
        # Verify the port exists in the list of all ports
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = [port['id'] for port in body['ports']
                 if port['id'] == self.port['id']]
        self.assertNotEmpty(ports, "Created port not found in the list")

    @attr(type='smoke')
    def test_port_list_filter_by_router_id(self):
        # Create a router
        network = self.create_network()
        self.create_subnet(network)
        router = self.create_router(data_utils.rand_name('router-'))
        resp, port = self.client.create_port(network_id=network['id'])
        # Add router interface to port created above
        resp, interface = self.client.add_router_interface_with_port_id(
            router['id'], port['port']['id'])
        self.addCleanup(self.client.remove_router_interface_with_port_id,
                        router['id'], port['port']['id'])
        # List ports filtered by router_id
        resp, port_list = self.client.list_ports(
            device_id=router['id'])
        self.assertEqual('200', resp['status'])
        ports = port_list['ports']
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['id'], port['port']['id'])
        self.assertEqual(ports[0]['device_id'], router['id'])

    @attr(type='smoke')
    def test_list_ports_fields(self):
        # Verify specific fields of ports
        resp, body = self.client.list_ports(fields='id')
        self.assertEqual('200', resp['status'])
        ports = body['ports']
        self.assertNotEmpty(ports, "Port list returned is empty")
        # Asserting the fields returned are correct
        for port in ports:
            self.assertEqual(len(port), 1)
            self.assertIn('id', port)


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
        networks_list = [network['id'] for network in body['networks']]
        for n in created_networks:
            self.assertIsNotNone(n['id'])
            self.assertIn(n['id'], networks_list)

    @attr(type='smoke')
    def test_bulk_create_delete_subnet(self):
        # Creates 2 subnets in one request
        cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cidrs = [subnet_cidr for subnet_cidr in cidr.subnet(mask_bits)]
        networks = [self.network1['id'], self.network2['id']]
        names = [data_utils.rand_name('subnet-') for i in range(len(networks))]
        subnets_list = []
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

    @attr(type='smoke')
    def test_bulk_create_delete_port(self):
        # Creates 2 ports in one request
        networks = [self.network1['id'], self.network2['id']]
        names = [data_utils.rand_name('port-') for i in range(len(networks))]
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
        super(NetworksIpV6TestJSON, cls).setUpClass()
        if not CONF.network_feature_enabled.ipv6:
            cls.tearDownClass()
            skip_msg = "IPv6 Tests are disabled."
            raise cls.skipException(skip_msg)


class NetworksIpV6TestXML(NetworksIpV6TestJSON):
    _interface = 'xml'
