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

import ipaddress

import netaddr
import six
import testtools

from tempest.api.network import base_security_groups as sec_base
from tempest.common import custom_matchers
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class PortsTestJSON(sec_base.BaseSecGroupTest):
    """Test the following operations for ports:

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
        self.ports_client.delete_port(port_id)
        body = self.ports_client.list_ports()
        ports_list = body['ports']
        self.assertFalse(port_id in [n['id'] for n in ports_list])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('c72c1c0c-2193-4aca-aaa4-b1442640f51c')
    def test_create_update_delete_port(self):
        # Verify port creation
        body = self.ports_client.create_port(network_id=self.network['id'])
        port = body['port']
        # Schedule port deletion with verification upon test completion
        self.addCleanup(self._delete_port, port['id'])
        self.assertTrue(port['admin_state_up'])
        # Verify port update
        new_name = "New_Port"
        body = self.ports_client.update_port(port['id'],
                                             name=new_name,
                                             admin_state_up=False)
        updated_port = body['port']
        self.assertEqual(updated_port['name'], new_name)
        self.assertFalse(updated_port['admin_state_up'])

    @decorators.idempotent_id('67f1b811-f8db-43e2-86bd-72c074d4a42c')
    def test_create_bulk_port(self):
        network1 = self.network
        network2 = self.create_network()
        network_list = [network1['id'], network2['id']]
        port_list = [{'network_id': net_id} for net_id in network_list]
        body = self.ports_client.create_bulk_ports(ports=port_list)
        created_ports = body['ports']
        port1 = created_ports[0]
        port2 = created_ports[1]
        self.addCleanup(self._delete_port, port1['id'])
        self.addCleanup(self._delete_port, port2['id'])
        self.assertEqual(port1['network_id'], network1['id'])
        self.assertEqual(port2['network_id'], network2['id'])
        self.assertTrue(port1['admin_state_up'])
        self.assertTrue(port2['admin_state_up'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('0435f278-40ae-48cb-a404-b8a087bc09b1')
    def test_create_port_in_allowed_allocation_pools(self):
        network = self.create_network()
        net_id = network['id']
        address = self.cidr
        address.prefixlen = self.mask_bits
        if ((address.version == 4 and address.prefixlen >= 30) or
           (address.version == 6 and address.prefixlen >= 126)):
            msg = ("Subnet %s isn't large enough for the test" % address.cidr)
            raise exceptions.InvalidConfiguration(msg)
        allocation_pools = {'allocation_pools': [{'start': str(address[2]),
                                                  'end': str(address[-2])}]}
        subnet = self.create_subnet(network, cidr=address,
                                    mask_bits=address.prefixlen,
                                    **allocation_pools)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        body = self.ports_client.create_port(network_id=net_id)
        self.addCleanup(self.ports_client.delete_port, body['port']['id'])
        port = body['port']
        ip_address = port['fixed_ips'][0]['ip_address']
        start_ip_address = allocation_pools['allocation_pools'][0]['start']
        end_ip_address = allocation_pools['allocation_pools'][0]['end']
        ip_range = netaddr.IPRange(start_ip_address, end_ip_address)
        self.assertIn(ip_address, ip_range)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('c9a685bd-e83f-499c-939f-9f7863ca259f')
    def test_show_port(self):
        # Verify the details of port
        body = self.ports_client.show_port(self.port['id'])
        port = body['port']
        self.assertIn('id', port)
        # NOTE(rfolco): created_at and updated_at may get inconsistent values
        # due to possible delay between POST request and resource creation.
        # TODO(rfolco): Neutron Bug #1365341 is fixed, can remove the key
        # extra_dhcp_opts in the O release (K/L gate jobs still need it).
        self.assertThat(self.port,
                        custom_matchers.MatchesDictExceptForKeys
                        (port, excluded_keys=['extra_dhcp_opts',
                                              'created_at',
                                              'updated_at']))

    @decorators.idempotent_id('45fcdaf2-dab0-4c13-ac6c-fcddfb579dbd')
    def test_show_port_fields(self):
        # Verify specific fields of a port
        fields = ['id', 'mac_address']
        body = self.ports_client.show_port(self.port['id'],
                                           fields=fields)
        port = body['port']
        self.assertEqual(sorted(port.keys()), sorted(fields))
        for field_name in fields:
            self.assertEqual(port[field_name], self.port[field_name])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('cf95b358-3e92-4a29-a148-52445e1ac50e')
    def test_list_ports(self):
        # Verify the port exists in the list of all ports
        body = self.ports_client.list_ports()
        ports = [port['id'] for port in body['ports']
                 if port['id'] == self.port['id']]
        self.assertNotEmpty(ports, "Created port not found in the list")

    @decorators.idempotent_id('e7fe260b-1e79-4dd3-86d9-bec6a7959fc5')
    def test_port_list_filter_by_ip(self):
        # Create network and subnet
        network = self.create_network()
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        # Create two ports
        port_1 = self.ports_client.create_port(network_id=network['id'])
        self.addCleanup(self.ports_client.delete_port, port_1['port']['id'])
        port_2 = self.ports_client.create_port(network_id=network['id'])
        self.addCleanup(self.ports_client.delete_port, port_2['port']['id'])
        # List ports filtered by fixed_ips
        port_1_fixed_ip = port_1['port']['fixed_ips'][0]['ip_address']
        fixed_ips = 'ip_address=' + port_1_fixed_ip
        port_list = self.ports_client.list_ports(fixed_ips=fixed_ips)
        # Check that we got the desired port
        ports = port_list['ports']
        tenant_ids = set([port['tenant_id'] for port in ports])
        self.assertEqual(len(tenant_ids), 1,
                         'Ports from multiple tenants are in the list resp')
        port_ids = [port['id'] for port in ports]
        fixed_ips = [port['fixed_ips'] for port in ports]
        port_ips = []
        for addr in fixed_ips:
            port_ips.extend([port['ip_address'] for port in addr])

        port_net_ids = [port['network_id'] for port in ports]
        self.assertIn(port_1['port']['id'], port_ids)
        self.assertIn(port_1_fixed_ip, port_ips)
        self.assertIn(network['id'], port_net_ids)

    @decorators.idempotent_id('79895408-85d5-460d-94e7-9531c5fd9123')
    @testtools.skipUnless(
        utils.is_extension_enabled('ip-substring-filtering', 'network'),
        'ip-substring-filtering extension not enabled.')
    def test_port_list_filter_by_ip_substr(self):
        # Create network and subnet
        network = self.create_network()
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])

        # Get two IP addresses
        ip_address_1 = None
        ip_address_2 = None
        ip_network = ipaddress.ip_network(six.text_type(subnet['cidr']))
        for ip in ip_network:
            if ip == ip_network.network_address:
                continue
            if ip_address_1 is None:
                ip_address_1 = six.text_type(ip)
            else:
                ip_address_2 = ip_address_1
                ip_address_1 = six.text_type(ip)
                # Make sure these two IP addresses have different substring
                if ip_address_1[:-1] != ip_address_2[:-1]:
                    break

        # Create two ports
        fixed_ips = [{'subnet_id': subnet['id'], 'ip_address': ip_address_1}]
        port_1 = self.ports_client.create_port(network_id=network['id'],
                                               fixed_ips=fixed_ips)
        self.addCleanup(self.ports_client.delete_port, port_1['port']['id'])
        fixed_ips = [{'subnet_id': subnet['id'], 'ip_address': ip_address_2}]
        port_2 = self.ports_client.create_port(network_id=network['id'],
                                               fixed_ips=fixed_ips)
        self.addCleanup(self.ports_client.delete_port, port_2['port']['id'])

        # Scenario 1: List port1 (port2 is filtered out)
        if ip_address_1[:-1] != ip_address_2[:-1]:
            ips_filter = 'ip_address_substr=' + ip_address_1[:-1]
        else:
            ips_filter = 'ip_address_substr=' + ip_address_1
        ports = self.ports_client.list_ports(fixed_ips=ips_filter)['ports']
        # Check that we got the desired port
        port_ids = [port['id'] for port in ports]
        fixed_ips = [port['fixed_ips'] for port in ports]
        port_ips = []
        for addr in fixed_ips:
            port_ips.extend([a['ip_address'] for a in addr])

        port_net_ids = [port['network_id'] for port in ports]
        self.assertIn(network['id'], port_net_ids)
        self.assertIn(port_1['port']['id'], port_ids)
        self.assertIn(port_1['port']['fixed_ips'][0]['ip_address'], port_ips)
        self.assertNotIn(port_2['port']['id'], port_ids)
        self.assertNotIn(
            port_2['port']['fixed_ips'][0]['ip_address'], port_ips)

        # Scenario 2: List both port1 and port2
        substr = ip_address_1
        while substr not in ip_address_2:
            substr = substr[:-1]
        ips_filter = 'ip_address_substr=' + substr
        ports = self.ports_client.list_ports(fixed_ips=ips_filter)['ports']
        # Check that we got both port
        port_ids = [port['id'] for port in ports]
        fixed_ips = [port['fixed_ips'] for port in ports]
        port_ips = []
        for addr in fixed_ips:
            port_ips.extend([a['ip_address'] for a in addr])

        port_net_ids = [port['network_id'] for port in ports]
        self.assertIn(network['id'], port_net_ids)
        self.assertIn(port_1['port']['id'], port_ids)
        self.assertIn(port_1['port']['fixed_ips'][0]['ip_address'], port_ips)
        self.assertIn(port_2['port']['id'], port_ids)
        self.assertIn(port_2['port']['fixed_ips'][0]['ip_address'], port_ips)

    @decorators.idempotent_id('5ad01ed0-0e6e-4c5d-8194-232801b15c72')
    def test_port_list_filter_by_router_id(self):
        # Create a router
        network = self.create_network()
        self.addCleanup(self.networks_client.delete_network, network['id'])
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        router = self.create_router()
        self.addCleanup(self.routers_client.delete_router, router['id'])
        port = self.ports_client.create_port(network_id=network['id'])
        # Add router interface to port created above
        self.routers_client.add_router_interface(router['id'],
                                                 port_id=port['port']['id'])
        self.addCleanup(self.routers_client.remove_router_interface,
                        router['id'], port_id=port['port']['id'])
        # List ports filtered by router_id
        port_list = self.ports_client.list_ports(device_id=router['id'])
        ports = port_list['ports']
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['id'], port['port']['id'])
        self.assertEqual(ports[0]['device_id'], router['id'])

    @decorators.idempotent_id('ff7f117f-f034-4e0e-abff-ccef05c454b4')
    def test_list_ports_fields(self):
        # Verify specific fields of ports
        fields = ['id', 'mac_address']
        body = self.ports_client.list_ports(fields=fields)
        ports = body['ports']
        self.assertNotEmpty(ports, "Port list returned is empty")
        # Asserting the fields returned are correct
        for port in ports:
            self.assertEqual(sorted(fields), sorted(port.keys()))

    @decorators.idempotent_id('63aeadd4-3b49-427f-a3b1-19ca81f06270')
    def test_create_update_port_with_second_ip(self):
        # Create a network with two subnets
        network = self.create_network()
        self.addCleanup(self.networks_client.delete_network, network['id'])
        subnet_1 = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet_1['id'])
        subnet_2 = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet_2['id'])
        fixed_ip_1 = [{'subnet_id': subnet_1['id']}]
        fixed_ip_2 = [{'subnet_id': subnet_2['id']}]

        fixed_ips = fixed_ip_1 + fixed_ip_2

        # Create a port with multiple IP addresses
        port = self.create_port(network,
                                fixed_ips=fixed_ips)
        self.addCleanup(self.ports_client.delete_port, port['id'])
        self.assertEqual(2, len(port['fixed_ips']))
        check_fixed_ips = [subnet_1['id'], subnet_2['id']]
        for item in port['fixed_ips']:
            self.assertIn(item['subnet_id'], check_fixed_ips)

        # Update the port to return to a single IP address
        port = self.update_port(port, fixed_ips=fixed_ip_1)
        self.assertEqual(1, len(port['fixed_ips']))

        # Update the port with a second IP address from second subnet
        port = self.update_port(port, fixed_ips=fixed_ips)
        self.assertEqual(2, len(port['fixed_ips']))

    def _update_port_with_security_groups(self, security_groups_names):
        subnet_1 = self.create_subnet(self.network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet_1['id'])
        fixed_ip_1 = [{'subnet_id': subnet_1['id']}]

        security_groups_list = list()
        sec_grps_client = self.security_groups_client
        for name in security_groups_names:
            group_create_body = sec_grps_client.create_security_group(
                name=name)
            self.addCleanup(self.security_groups_client.delete_security_group,
                            group_create_body['security_group']['id'])
            security_groups_list.append(group_create_body['security_group']
                                        ['id'])
        # Create a port
        sec_grp_name = data_utils.rand_name('secgroup')
        security_group = sec_grps_client.create_security_group(
            name=sec_grp_name)
        self.addCleanup(self.security_groups_client.delete_security_group,
                        security_group['security_group']['id'])
        post_body = {
            "name": data_utils.rand_name('port-'),
            "security_groups": [security_group['security_group']['id']],
            "network_id": self.network['id'],
            "admin_state_up": True,
            "fixed_ips": fixed_ip_1}
        body = self.ports_client.create_port(**post_body)
        self.addCleanup(self.ports_client.delete_port, body['port']['id'])
        port = body['port']

        # Update the port with security groups
        subnet_2 = self.create_subnet(self.network)
        fixed_ip_2 = [{'subnet_id': subnet_2['id']}]
        update_body = {"name": data_utils.rand_name('port-'),
                       "admin_state_up": False,
                       "fixed_ips": fixed_ip_2,
                       "security_groups": security_groups_list}
        body = self.ports_client.update_port(port['id'], **update_body)
        port_show = body['port']
        # Verify the security groups and other attributes updated to port
        exclude_keys = set(port_show).symmetric_difference(update_body)
        exclude_keys.add('fixed_ips')
        exclude_keys.add('security_groups')
        self.assertThat(port_show, custom_matchers.MatchesDictExceptForKeys(
                        update_body, exclude_keys))
        self.assertEqual(fixed_ip_2[0]['subnet_id'],
                         port_show['fixed_ips'][0]['subnet_id'])

        for security_group in security_groups_list:
            self.assertIn(security_group, port_show['security_groups'])

    @decorators.idempotent_id('58091b66-4ff4-4cc1-a549-05d60c7acd1a')
    @testtools.skipUnless(
        utils.is_extension_enabled('security-group', 'network'),
        'security-group extension not enabled.')
    def test_update_port_with_security_group_and_extra_attributes(self):
        self._update_port_with_security_groups(
            [data_utils.rand_name('secgroup')])

    @decorators.idempotent_id('edf6766d-3d40-4621-bc6e-2521a44c257d')
    @testtools.skipUnless(
        utils.is_extension_enabled('security-group', 'network'),
        'security-group extension not enabled.')
    def test_update_port_with_two_security_groups_and_extra_attributes(self):
        self._update_port_with_security_groups(
            [data_utils.rand_name('secgroup'),
             data_utils.rand_name('secgroup')])

    @decorators.idempotent_id('13e95171-6cbd-489c-9d7c-3f9c58215c18')
    def test_create_show_delete_port_user_defined_mac(self):
        # Create a port for a legal mac
        body = self.ports_client.create_port(network_id=self.network['id'])
        old_port = body['port']
        free_mac_address = old_port['mac_address']
        self.ports_client.delete_port(old_port['id'])
        # Create a new port with user defined mac
        body = self.ports_client.create_port(network_id=self.network['id'],
                                             mac_address=free_mac_address)
        self.addCleanup(self.ports_client.delete_port, body['port']['id'])
        port = body['port']
        body = self.ports_client.show_port(port['id'])
        show_port = body['port']
        self.assertEqual(free_mac_address,
                         show_port['mac_address'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('4179dcb9-1382-4ced-84fe-1b91c54f5735')
    @testtools.skipUnless(
        utils.is_extension_enabled('security-group', 'network'),
        'security-group extension not enabled.')
    def test_create_port_with_no_securitygroups(self):
        network = self.create_network()
        self.addCleanup(self.networks_client.delete_network, network['id'])
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        port = self.create_port(network, security_groups=[])
        self.addCleanup(self.ports_client.delete_port, port['id'])
        self.assertIsNotNone(port['security_groups'])
        self.assertEmpty(port['security_groups'])


class PortsIpV6TestJSON(PortsTestJSON):
    _ip_version = 6
