# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import sys

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute.base import BaseComputeTest


class ServersNegativeTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        raise cls.skipException("Until Bug 1046870 is fixed")
        super(ServersNegativeTest, cls).setUpClass()
        cls.client = cls.servers_client
        cls.img_client = cls.images_client
        cls.alt_os = clients.AltManager()
        cls.alt_client = cls.alt_os.servers_client

    @attr(type='negative')
    def test_server_name_blank(self):
        # Create a server with name parameter empty
        try:
                resp, server = self.create_server_with_extras('',
                                                              self.image_ref,
                                                              self.flavor_ref)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Server name cannot be blank')

    @attr(type='negative')
    def test_personality_file_contents_not_encoded(self):
        # Use an unencoded file when creating a server with personality
        file_contents = 'This is a test file.'
        person = [{'path': '/etc/testfile.txt',
                   'contents': file_contents}]

        try:
            resp, server = self.create_server_with_extras('test',
                                                          self.image_ref,
                                                          self.flavor_ref,
                                                          personality=person)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Unencoded file contents should not be accepted')

    @attr(type='negative')
    def test_create_with_invalid_image(self):
        # Create a server with an unknown image
        try:
            resp, server = self.create_server_with_extras('fail', -1,
                                                          self.flavor_ref)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Cannot create a server with an invalid image')

    @attr(type='negative')
    def test_create_with_invalid_flavor(self):
        # Create a server with an unknown flavor
        try:
            self.create_server_with_extras('fail', self.image_ref, -1)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Cannot create a server with an invalid flavor')

    @attr(type='negative')
    def test_invalid_access_ip_v4_address(self):
        # An access IPv4 address must match a valid address pattern
        IPv4 = '1.1.1.1.1.1'
        name = rand_name('server')
        try:
            resp, server = self.create_server_with_extras(name,
                                                          self.image_ref,
                                                          self.flavor_ref,
                                                          accessIPv4=IPv4)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Access IPv4 address must match the correct format')

    @attr(type='negative')
    def test_invalid_ip_v6_address(self):
        # An access IPv6 address must match a valid address pattern
        IPv6 = 'notvalid'
        name = rand_name('server')
        try:
            resp, server = self.create_server_with_extras(name,
                                                          self.image_ref,
                                                          self.flavor_ref,
                                                          accessIPv6=IPv6)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Access IPv6 address must match the correct format')

    @attr(type='negative')
    def test_reboot_deleted_server(self):
        # Reboot a deleted server
        self.name = rand_name('server')
        resp, create_server = self.create_server_with_extras(self.name,
                                                             self.image_ref,
                                                             self.flavor_ref)
        self.server_id = create_server['id']
        self.client.delete_server(self.server_id)
        self.client.wait_for_server_termination(self.server_id)
        try:
            resp1, reboot_server = self.client.reboot(self.server_id, 'SOFT')
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to reboot a deleted server')

    @attr(type='negative')
    def test_rebuild_deleted_server(self):
        # Rebuild a deleted server
        self.name = rand_name('server')
        resp, create_server = self.create_server_with_extras(self.name,
                                                             self.image_ref,
                                                             self.flavor_ref)
        self.server_id = create_server['id']
        self.client.delete_server(self.server_id)
        self.client.wait_for_server_termination(self.server_id)
        try:
            resp1, rebuild_server = self.client.rebuild(self.server_id,
                                                        self.image_ref_alt)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to rebuild a deleted server')

    @attr(type='negative')
    def test_create_numeric_server_name(self):
        # Create a server with a numeric name

        server_name = 12345
        self.assertRaises(exceptions.BadRequest,
                          self.create_server_with_extras,
                          server_name, self.image_ref, self.flavor_ref)

    @attr(type='negative')
    def test_create_server_name_length_exceeds_256(self):
        # Create a server with name length exceeding 256 characters

        server_name = 'a' * 256
        self.assertRaises(exceptions.BadRequest,
                          self.create_server_with_extras,
                          server_name, self.image_ref, self.flavor_ref)

    @attr(type='negative')
    def test_create_with_invalid_network_uuid(self):
        # Pass invalid network uuid while creating a server

        server_name = rand_name('server')
        networks = [{'fixed_ip': '10.0.1.1', 'uuid': 'a-b-c-d-e-f-g-h-i-j'}]

        self.assertRaises(exceptions.BadRequest,
                          self.create_server_with_extras,
                          server_name, self.image_ref, self.flavor_ref,
                          networks=networks)

    @attr(type='negative')
    def test_create_with_non_existant_keypair(self):
        # Pass a non existant keypair while creating a server

        key_name = rand_name('key')
        server_name = rand_name('server')
        self.assertRaises(exceptions.BadRequest,
                          self.create_server_with_extras,
                          server_name, self.image_ref, self.flavor_ref,
                          key_name=key_name)

    @attr(type='negative')
    def test_create_server_metadata_exceeds_length_limit(self):
        # Pass really long metadata while creating a server

        server_name = rand_name('server')
        metadata = {'a': 'b' * 260}
        self.assertRaises(exceptions.OverLimit,
                          self.create_server_with_extras,
                          server_name, self.image_ref, self.flavor_ref,
                          meta=metadata)

    @attr(type='negative')
    def test_update_name_of_non_existent_server(self):
        # Update name of a non-existent server

        server_name = rand_name('server')
        new_name = rand_name('server') + '_updated'

        self.assertRaises(exceptions.NotFound, self.client.update_server,
                          server_name, name=new_name)

    @attr(type='negative')
    def test_update_server_set_empty_name(self):
        # Update name of the server to an empty string

        server_name = rand_name('server')
        new_name = ''

        self.assertRaises(exceptions.BadRequest, self.client.update_server,
                          server_name, name=new_name)

    @attr(type='negative')
    def test_update_server_of_another_tenant(self):
        # Update name of a server that belongs to another tenant

        server = self.create_server()
        new_name = server['id'] + '_new'
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.update_server, server['id'],
                          name=new_name)

    @attr(type='negative')
    def test_update_server_name_length_exceeds_256(self):
        # Update name of server exceed the name length limit

        server = self.create_server()
        new_name = 'a' * 256
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_server,
                          server['id'],
                          name=new_name)

    @attr(type='negative')
    def test_delete_non_existent_server(self):
        # Delete a non existent server

        self.assertRaises(exceptions.NotFound, self.client.delete_server,
                          '999erra43')

    @attr(type='negative')
    def test_delete_a_server_of_another_tenant(self):
        # Delete a server that belongs to another tenant
        try:
            server = self.create_server()
            self.assertRaises(exceptions.NotFound,
                              self.alt_client.delete_server,
                              server['id'])
        finally:
            self.client.delete_server(server['id'])

    @attr(type='negative')
    def test_delete_server_pass_negative_id(self):
        # Pass an invalid string parameter to delete server

        self.assertRaises(exceptions.NotFound, self.client.delete_server, -1)

    @attr(type='negative')
    def test_delete_server_pass_id_exceeding_length_limit(self):
        # Pass a server ID that exceeds length limit to delete server

        self.assertRaises(exceptions.NotFound, self.client.delete_server,
                          sys.maxint + 1)
