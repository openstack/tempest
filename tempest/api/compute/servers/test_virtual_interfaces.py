# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.test import attr
from tempest.test import skip_because


class VirtualInterfacesTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    CONF = config.CONF

    @classmethod
    def setUpClass(cls):
        super(VirtualInterfacesTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    @skip_because(bug="1183436",
                  condition=CONF.service_available.neutron)
    @attr(type='gate')
    def test_list_virtual_interfaces(self):
        # Positive test:Should be able to GET the virtual interfaces list
        # for a given server_id
        resp, output = self.client.list_virtual_interfaces(self.server_id)
        self.assertEqual(200, resp.status)
        self.assertIsNotNone(output)
        virt_ifaces = output
        self.assertNotEqual(0, len(virt_ifaces['virtual_interfaces']),
                            'Expected virtual interfaces, got 0 interfaces.')
        for virt_iface in virt_ifaces['virtual_interfaces']:
            mac_address = virt_iface['mac_address']
            self.assertTrue(netaddr.valid_mac(mac_address),
                            "Invalid mac address detected.")

    @attr(type=['negative', 'gate'])
    def test_list_virtual_interfaces_invalid_server_id(self):
        # Negative test: Should not be able to GET virtual interfaces
        # for an invalid server_id
        invalid_server_id = data_utils.rand_name('!@#$%^&*()')
        self.assertRaises(exceptions.NotFound,
                          self.client.list_virtual_interfaces,
                          invalid_server_id)


class VirtualInterfacesTestXML(VirtualInterfacesTestJSON):
    _interface = 'xml'
