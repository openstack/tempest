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

from tempest.api.network import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class PortsAdminExtendedAttrsTestJSON(base.BaseAdminNetworkTest):

    @classmethod
    def setup_clients(cls):
        super(PortsAdminExtendedAttrsTestJSON, cls).setup_clients()
        cls.hyper_client = cls.os_admin.hypervisor_client

    @classmethod
    def resource_setup(cls):
        super(PortsAdminExtendedAttrsTestJSON, cls).resource_setup()
        cls.network = cls.create_network()
        hyper_list = cls.hyper_client.list_hypervisors()
        cls.host_id = hyper_list['hypervisors'][0]['hypervisor_hostname']

    @decorators.idempotent_id('8e8569c1-9ac7-44db-8bc1-f5fb2814f29b')
    def test_create_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id'],
                     "binding:host_id": self.host_id}
        body = self.admin_ports_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_ports_client.delete_port, port['id'])
        host_id = port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @decorators.idempotent_id('6f6c412c-711f-444d-8502-0ac30fbf5dd5')
    def test_update_port_binding_ext_attr(self):
        post_body = {"network_id": self.network['id']}
        body = self.admin_ports_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_ports_client.delete_port, port['id'])
        update_body = {"binding:host_id": self.host_id}
        body = self.admin_ports_client.update_port(port['id'], **update_body)
        updated_port = body['port']
        host_id = updated_port['binding:host_id']
        self.assertIsNotNone(host_id)
        self.assertEqual(self.host_id, host_id)

    @decorators.idempotent_id('1c82a44a-6c6e-48ff-89e1-abe7eaf8f9f8')
    def test_list_ports_binding_ext_attr(self):
        # Create a new port
        post_body = {"network_id": self.network['id']}
        body = self.admin_ports_client.create_port(**post_body)
        port = body['port']
        self.addCleanup(self.admin_ports_client.delete_port, port['id'])

        # Update the port's binding attributes so that is now 'bound'
        # to a host
        update_body = {"binding:host_id": self.host_id}
        self.admin_ports_client.update_port(port['id'], **update_body)

        # List all ports, ensure new port is part of list and its binding
        # attributes are set and accurate
        body = self.admin_ports_client.list_ports()
        ports_list = body['ports']
        pids_list = [p['id'] for p in ports_list]
        self.assertIn(port['id'], pids_list)
        listed_port = [p for p in ports_list if p['id'] == port['id']]
        self.assertEqual(1, len(listed_port),
                         'Multiple ports listed with id %s in ports listing: '
                         '%s' % (port['id'], ports_list))
        self.assertEqual(self.host_id, listed_port[0]['binding:host_id'])

    @decorators.idempotent_id('b54ac0ff-35fc-4c79-9ca3-c7dbd4ea4f13')
    def test_show_port_binding_ext_attr(self):
        body = self.admin_ports_client.create_port(
            network_id=self.network['id'])
        port = body['port']
        self.addCleanup(self.admin_ports_client.delete_port, port['id'])
        body = self.admin_ports_client.show_port(port['id'])
        show_port = body['port']
        self.assertEqual(port['binding:host_id'],
                         show_port['binding:host_id'])
        self.assertEqual(port['binding:vif_type'],
                         show_port['binding:vif_type'])
        self.assertEqual(port['binding:vif_details'],
                         show_port['binding:vif_details'])


class PortsAdminExtendedAttrsIpV6TestJSON(PortsAdminExtendedAttrsTestJSON):
    _ip_version = 6
