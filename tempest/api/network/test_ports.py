# Copyright 2014 OpenStack Foundation
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
import socket

from tempest.api.network import base
from tempest.common import custom_matchers
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class PortsTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Test the following operations for ports:

        port create
        port delete
        port list
        port show
        port update
    """

    @classmethod
    def resource_setup(cls):
        super(PortsTestJSON, cls).resource_setup()
        cls.network = cls.create_network()
        cls.port = cls.create_port(cls.network)

    def _delete_port(self, port_id):
        self.client.delete_port(port_id)
        body = self.client.list_ports()
        ports_list = body['ports']
        self.assertFalse(port_id in [n['id'] for n in ports_list])

    @test.attr(type='smoke')
    def test_create_update_delete_port(self):
        # Verify port creation
        body = self.client.create_port(network_id=self.network['id'])
        port = body['port']
        # Schedule port deletion with verification upon test completion
        self.addCleanup(self._delete_port, port['id'])
        self.assertTrue(port['admin_state_up'])
        # Verify port update
        new_name = "New_Port"
        body = self.client.update_port(port['id'],
                                       name=new_name,
                                       admin_state_up=False)
        updated_port = body['port']
        self.assertEqual(updated_port['name'], new_name)
        self.assertFalse(updated_port['admin_state_up'])

    def test_create_bulk_port(self):
        network1 = self.network
        name = data_utils.rand_name('network-')
        network2 = self.create_network(network_name=name)
        network_list = [network1['id'], network2['id']]
        port_list = [{'network_id': net_id} for net_id in network_list]
        body = self.client.create_bulk_port(port_list)
        created_ports = body['ports']
        port1 = created_ports[0]
        port2 = created_ports[1]
        self.addCleanup(self._delete_port, port1['id'])
        self.addCleanup(self._delete_port, port2['id'])
        self.assertEqual(port1['network_id'], network1['id'])
        self.assertEqual(port2['network_id'], network2['id'])
        self.assertTrue(port1['admin_state_up'])
        self.assertTrue(port2['admin_state_up'])

    @classmethod
    def _get_ipaddress_from_tempest_conf(cls):
        """Return first subnet gateway for configured CIDR """
        if cls._ip_version == 4:
            cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)

        elif cls._ip_version == 6:
            cidr = netaddr.IPNetwork(CONF.network.tenant_network_v6_cidr)

        return netaddr.IPAddress(cidr)

    @test.attr(type='smoke')
    def test_create_port_in_allowed_allocation_pools(self):
        network = self.create_network()
        net_id = network['id']
        address = self._get_ipaddress_from_tempest_conf()
        allocation_pools = {'allocation_pools': [{'start': str(address + 4),
                                                  'end': str(address + 6)}]}
        self.create_subnet(network, **allocation_pools)
        body = self.client.create_port(network_id=net_id)
        self.addCleanup(self.client.delete_port, body['port']['id'])
        port = body['port']
        ip_address = port['fixed_ips'][0]['ip_address']
        start_ip_address = allocation_pools['allocation_pools'][0]['start']
        end_ip_address = allocation_pools['allocation_pools'][0]['end']
        ip_range = netaddr.IPRange(start_ip_address, end_ip_address)
        self.assertIn(ip_address, ip_range)

    @test.attr(type='smoke')
    def test_show_port(self):
        # Verify the details of port
        body = self.client.show_port(self.port['id'])
        port = body['port']
        self.assertIn('id', port)
        # TODO(Santosh)- This is a temporary workaround to compare create_port
        # and show_port dict elements.Remove this once extra_dhcp_opts issue
        # gets fixed in neutron.( bug - 1365341.)
        self.assertThat(self.port,
                        custom_matchers.MatchesDictExceptForKeys
                        (port, excluded_keys=['extra_dhcp_opts']))

    @test.attr(type='smoke')
    def test_show_port_fields(self):
        # Verify specific fields of a port
        fields = ['id', 'mac_address']
        body = self.client.show_port(self.port['id'],
                                     fields=fields)
        port = body['port']
        self.assertEqual(sorted(port.keys()), sorted(fields))
        for field_name in fields:
            self.assertEqual(port[field_name], self.port[field_name])

    @test.attr(type='smoke')
    def test_list_ports(self):
        # Verify the port exists in the list of all ports
        body = self.client.list_ports()
        ports = [port['id'] for port in body['ports']
                 if port['id'] == self.port['id']]
        self.assertNotEmpty(ports, "Created port not found in the list")

    @test.attr(type='smoke')
    def test_port_list_filter_by_router_id(self):
        # Create a router
        network = self.create_network()
        self.create_subnet(network)
        router = self.create_router(data_utils.rand_name('router-'))
        port = self.client.create_port(network_id=network['id'])
        # Add router interface to port created above
        self.client.add_router_interface_with_port_id(
            router['id'], port['port']['id'])
        self.addCleanup(self.client.remove_router_interface_with_port_id,
                        router['id'], port['port']['id'])
        # List ports filtered by router_id
        port_list = self.client.list_ports(device_id=router['id'])
        ports = port_list['ports']
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['id'], port['port']['id'])
        self.assertEqual(ports[0]['device_id'], router['id'])

    @test.attr(type='smoke')
    def test_list_ports_fields(self):
        # Verify specific fields of ports
        fields = ['id', 'mac_address']
        body = self.client.list_ports(fields=fields)
        ports = body['ports']
        self.assertNotEmpty(ports, "Port list returned is empty")
        # Asserting the fields returned are correct
        for port in ports:
            self.assertEqual(sorted(fields), sorted(port.keys()))

    @test.attr(type='smoke')
    def test_update_port_with_second_ip(self):
        # Create a network with two subnets
        network = self.create_network()
        subnet_1 = self.create_subnet(network)
        subnet_2 = self.create_subnet(network)
        fixed_ip_1 = [{'subnet_id': subnet_1['id']}]
        fixed_ip_2 = [{'subnet_id': subnet_2['id']}]

        # Create a port with a single IP address from first subnet
        port = self.create_port(network,
                                fixed_ips=fixed_ip_1)
        self.assertEqual(1, len(port['fixed_ips']))

        # Update the port with a second IP address from second subnet
        fixed_ips = fixed_ip_1 + fixed_ip_2
        port = self.update_port(port, fixed_ips=fixed_ips)
        self.assertEqual(2, len(port['fixed_ips']))

        # Update the port to return to a single IP address
        port = self.update_port(port, fixed_ips=fixed_ip_1)
        self.assertEqual(1, len(port['fixed_ips']))

    def _update_port_with_security_groups(self, security_groups_names):
        post_body = {"network_id": self.network['id']}
        self.create_subnet(self.network)
        security_groups_list = list()
        for name in security_groups_names:
            group_create_body = self.client.create_security_group(
                name=name)
            self.addCleanup(self.client.delete_security_group,
                            group_create_body['security_group']['id'])
            security_groups_list.append(group_create_body['security_group']
                                        ['id'])
        # Create a port
        body = self.client.create_port(**post_body)
        self.addCleanup(self.client.delete_port, body['port']['id'])
        port = body['port']
        # Update the port with security groups
        update_body = {"security_groups": security_groups_list}
        body = self.client.update_port(port['id'], **update_body)
        # Verify the security groups updated to port
        port_show = body['port']
        for security_group in security_groups_list:
            self.assertIn(security_group, port_show['security_groups'])

    @test.attr(type='smoke')
    def test_update_port_with_security_group(self):
        self._update_port_with_security_groups(
            [data_utils.rand_name('secgroup')])

    @test.attr(type='smoke')
    def test_update_port_with_two_security_groups(self):
        self._update_port_with_security_groups(
            [data_utils.rand_name('secgroup'),
             data_utils.rand_name('secgroup')])

    @test.attr(type='smoke')
    def test_create_show_delete_port_user_defined_mac(self):
        # Create a port for a legal mac
        body = self.client.create_port(network_id=self.network['id'])
        old_port = body['port']
        free_mac_address = old_port['mac_address']
        self.client.delete_port(old_port['id'])
        # Create a new port with user defined mac
        body = self.client.create_port(network_id=self.network['id'],
                                       mac_address=free_mac_address)
        self.addCleanup(self.client.delete_port, body['port']['id'])
        port = body['port']
        body = self.client.show_port(port['id'])
        show_port = body['port']
        self.assertEqual(free_mac_address,
                         show_port['mac_address'])

    @test.attr(type='smoke')
    def test_create_port_with_no_securitygroups(self):
        network = self.create_network()
        self.create_subnet(network)
        port = self.create_port(network, security_groups=[])
        self.assertIsNotNone(port['security_groups'])
        self.assertEmpty(port['security_groups'])

    @test.attr(type='smoke')
    def test_update_port_with_no_securitygroups(self):
        network = self.create_network()
        self.create_subnet(network)
        port = self.create_port(network)
        # Verify that port is created with default security group
        self.assertIsNotNone(port['security_groups'])
        self.assertNotEmpty(port['security_groups'])
        updated_port = self.update_port(port, security_groups=[])
        self.assertIsNotNone(updated_port['security_groups'])
        self.assertEmpty(updated_port['security_groups'])


class PortsAdminExtendedAttrsTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def resource_setup(cls):
        super(PortsAdminExtendedAttrsTestJSON, cls).resource_setup()
        cls.identity_client = cls._get_identity_admin_client()
        cls.tenant = cls.identity_client.get_tenant_by_name(
            CONF.identity.tenant_name)
        cls.network = cls.create_network()
        cls.host_id = socket.gethostname()

    @test.attr(type='smoke')
    def test_create_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id'],
                     "binding:host_id": self.host_id}
        body = self.admin_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        host_id = port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @test.attr(type='smoke')
    def test_update_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id']}
        body = self.admin_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        update_body = {"binding:host_id": self.host_id}
        body = self.admin_client.update_port(port['id'], **update_body)
        updated_port = body['port']
        host_id = updated_port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @test.attr(type='smoke')
    def test_list_ports_binding_ext_attr(self):
        # Create a new port
        post_body = {"network_id": self.network['id']}
        body = self.admin_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])

        # Update the port's binding attributes so that is now 'bound'
        # to a host
        update_body = {"binding:host_id": self.host_id}
        self.admin_client.update_port(port['id'], **update_body)

        # List all ports, ensure new port is part of list and its binding
        # attributes are set and accurate
        body = self.admin_client.list_ports()
        ports_list = body['ports']
        pids_list = [p['id'] for p in ports_list]
        self.assertIn(port['id'], pids_list)
        listed_port = [p for p in ports_list if p['id'] == port['id']]
        self.assertEqual(1, len(listed_port),
                         'Multiple ports listed with id %s in ports listing: '
                         '%s' % (port['id'], ports_list))
        self.assertEqual(self.host_id, listed_port[0]['binding:host_id'])

    @test.attr(type='smoke')
    def test_show_port_binding_ext_attr(self):
        body = self.admin_client.create_port(network_id=self.network['id'])
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        body = self.admin_client.show_port(port['id'])
        show_port = body['port']
        self.assertEqual(port['binding:host_id'],
                         show_port['binding:host_id'])
        self.assertEqual(port['binding:vif_type'],
                         show_port['binding:vif_type'])
        self.assertEqual(port['binding:vif_details'],
                         show_port['binding:vif_details'])


class PortsIpV6TestJSON(PortsTestJSON):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr
    _tenant_network_mask_bits = CONF.network.tenant_network_v6_mask_bits


class PortsAdminExtendedAttrsIpV6TestJSON(PortsAdminExtendedAttrsTestJSON):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr
    _tenant_network_mask_bits = CONF.network.tenant_network_v6_mask_bits
