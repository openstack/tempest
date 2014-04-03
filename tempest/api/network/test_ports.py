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

import socket

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class PortsTestJSON(base.BaseNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(PortsTestJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.port = cls.create_port(cls.network)

    def _delete_port(self, port_id):
        resp, body = self.client.delete_port(port_id)
        self.assertEqual('204', resp['status'])
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports_list = body['ports']
        self.assertFalse(port_id in [n['id'] for n in ports_list])

    @test.attr(type='smoke')
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

    @test.attr(type='smoke')
    def test_show_port(self):
        # Verify the details of port
        resp, body = self.client.show_port(self.port['id'])
        self.assertEqual('200', resp['status'])
        port = body['port']
        self.assertIn('id', port)
        self.assertEqual(port['id'], self.port['id'])
        self.assertEqual(self.port['admin_state_up'], port['admin_state_up'])
        self.assertEqual(self.port['device_id'], port['device_id'])
        self.assertEqual(self.port['device_owner'], port['device_owner'])
        self.assertEqual(self.port['mac_address'], port['mac_address'])
        self.assertEqual(self.port['name'], port['name'])
        self.assertEqual(self.port['security_groups'],
                         port['security_groups'])
        self.assertEqual(self.port['network_id'], port['network_id'])
        self.assertEqual(self.port['security_groups'],
                         port['security_groups'])

    @test.attr(type='smoke')
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

    @test.attr(type='smoke')
    def test_list_ports(self):
        # Verify the port exists in the list of all ports
        resp, body = self.client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = [port['id'] for port in body['ports']
                 if port['id'] == self.port['id']]
        self.assertNotEmpty(ports, "Created port not found in the list")

    @test.attr(type='smoke')
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

    @test.attr(type='smoke')
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


class PortsTestXML(PortsTestJSON):
    _interface = 'xml'


class PortsAdminExtendedAttrsTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(PortsAdminExtendedAttrsTestJSON, cls).setUpClass()
        cls.identity_client = cls._get_identity_admin_client()
        cls.tenant = cls.identity_client.get_tenant_by_name(
            CONF.identity.tenant_name)
        cls.network = cls.create_network()
        cls.host_id = socket.gethostname()

    @test.attr(type='smoke')
    def test_create_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id'],
                     "binding:host_id": self.host_id}
        resp, body = self.admin_client.create_port(**post_body)
        self.assertEqual('201', resp['status'])
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        host_id = port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @test.attr(type='smoke')
    def test_update_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id']}
        resp, body = self.admin_client.create_port(**post_body)
        self.assertEqual('201', resp['status'])
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        update_body = {"binding:host_id": self.host_id}
        resp, body = self.admin_client.update_port(port['id'], **update_body)
        self.assertEqual('200', resp['status'])
        updated_port = body['port']
        host_id = updated_port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @test.attr(type='smoke')
    def test_list_ports_binding_ext_attr(self):
        # Create a new port
        post_body = {"network_id": self.network['id']}
        resp, body = self.admin_client.create_port(**post_body)
        self.assertEqual('201', resp['status'])
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])

        # Update the port's binding attributes so that is now 'bound'
        # to a host
        update_body = {"binding:host_id": self.host_id}
        resp, _ = self.admin_client.update_port(port['id'], **update_body)
        self.assertEqual('200', resp['status'])

        # List all ports, ensure new port is part of list and its binding
        # attributes are set and accurate
        resp, body = self.admin_client.list_ports()
        self.assertEqual('200', resp['status'])
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
        resp, body = self.admin_client.create_port(
            network_id=self.network['id'])
        self.assertEqual('201', resp['status'])
        port = body['port']
        self.addCleanup(self.admin_client.delete_port, port['id'])
        resp, body = self.admin_client.show_port(port['id'])
        self.assertEqual('200', resp['status'])
        show_port = body['port']
        self.assertEqual(port['binding:host_id'],
                         show_port['binding:host_id'])
        self.assertEqual(port['binding:vif_type'],
                         show_port['binding:vif_type'])
        self.assertEqual(port['binding:vif_details'],
                         show_port['binding:vif_details'])


class PortsAdminExtendedAttrsTestXML(PortsAdminExtendedAttrsTestJSON):
    _interface = 'xml'


class PortsIpV6TestJSON(PortsTestJSON):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr
    _tenant_network_mask_bits = CONF.network.tenant_network_v6_mask_bits

    @classmethod
    def setUpClass(cls):
        super(PortsIpV6TestJSON, cls).setUpClass()
        if not CONF.network_feature_enabled.ipv6:
            cls.tearDownClass()
            skip_msg = "IPv6 Tests are disabled."
            raise cls.skipException(skip_msg)


class PortsIpV6TestXML(PortsIpV6TestJSON):
    _interface = 'xml'


class PortsAdminExtendedAttrsIpV6TestJSON(PortsAdminExtendedAttrsTestJSON):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr
    _tenant_network_mask_bits = CONF.network.tenant_network_v6_mask_bits

    @classmethod
    def setUpClass(cls):
        super(PortsAdminExtendedAttrsIpV6TestJSON, cls).setUpClass()
        if not CONF.network_feature_enabled.ipv6:
            cls.tearDownClass()
            skip_msg = "IPv6 Tests are disabled."
            raise cls.skipException(skip_msg)


class PortsAdminExtendedAttrsIpV6TestXML(
    PortsAdminExtendedAttrsIpV6TestJSON):
    _interface = 'xml'
