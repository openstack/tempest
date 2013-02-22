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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base


@attr(type='smoke')
class VirtualInterfacesTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VirtualInterfacesTestJSON, cls).setUpClass()
        cls.name = rand_name('server')
        cls.client = cls.servers_client
        resp, server = cls.servers_client.create_server(cls.name,
                                                        cls.image_ref,
                                                        cls.flavor_ref)
        cls.server_id = server['id']

        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.servers_client.delete_server(cls.server_id)
        super(VirtualInterfacesTestJSON, cls).tearDownClass()

    @attr(type='positive')
    def test_list_virtual_interfaces(self):
        # Positive test:Should be able to GET the virtual interfaces list
        # for a given server_id
        resp, output = self.client.list_virtual_interfaces(self.server_id)
        self.assertEqual(200, resp.status)
        self.assertNotEqual(output, None)
        virtual_interfaces = output
        self.assertNotEqual(0, len(virtual_interfaces),
                            'Expected virtual interfaces, got zero.')

    @attr(type='negative')
    def test_list_virtual_interfaces_invalid_server_id(self):
        # Negative test: Should not be able to GET virtual interfaces
        # for an invalid server_id
        try:
            resp, output = self.client.list_virtual_interfaces('!@#$%^&*()')
        except exceptions.NotFound:
            pass


@attr(type='smoke')
class VirtualInterfacesTestXML(VirtualInterfacesTestJSON):
    _interface = 'xml'
