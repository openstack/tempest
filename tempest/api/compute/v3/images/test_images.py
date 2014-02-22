# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class ImagesV3Test(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ImagesV3Test, cls).setUpClass()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

    def __create_image__(self, server_id, name, meta=None):
        resp, body = self.servers_client.create_image(server_id, name, meta)
        image_id = data_utils.parse_image_id(resp['location'])
        self.addCleanup(self.client.delete_image, image_id)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        return resp, body

    @test.attr(type=['negative', 'gate'])
    def test_create_image_from_deleted_server(self):
        # An image should not be created if the server instance is removed
        resp, server = self.create_test_server(wait_until='ACTIVE')

        # Delete server before trying to create server
        self.servers_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])
        # Create a new image after server is deleted
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        self.assertRaises(exceptions.NotFound,
                          self.__create_image__,
                          server['id'], name, meta)

    @test.attr(type=['negative', 'gate'])
    def test_create_image_from_invalid_server(self):
        # An image should not be created with invalid server id
        # Create a new image with invalid server id
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        resp = {}
        resp['status'] = None
        self.assertRaises(exceptions.NotFound, self.__create_image__,
                          '!@#$%^&*()', name, meta)

    @test.attr(type=['negative', 'gate'])
    def test_create_image_from_stopped_server(self):
        resp, server = self.create_test_server(wait_until='ACTIVE')
        self.servers_client.stop(server['id'])
        self.servers_client.wait_for_server_status(server['id'],
                                                   'SHUTOFF')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        snapshot_name = data_utils.rand_name('test-snap-')
        resp, image = self.create_image_from_server(server['id'],
                                                    name=snapshot_name,
                                                    wait_until='active')
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertEqual(snapshot_name, image['name'])

    @test.attr(type='gate')
    def test_delete_queued_image(self):
        snapshot_name = data_utils.rand_name('test-snap-')
        resp, server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        resp, image = self.create_image_from_server(server['id'],
                                                    name=snapshot_name,
                                                    wait_until='queued')
        resp, body = self.client.delete_image(image['id'])
        self.assertEqual('200', resp['status'])

    @test.attr(type=['negative', 'gate'])
    def test_create_image_specify_uuid_35_characters_or_less(self):
        # Return an error if Image ID passed is 35 characters or less
        snapshot_name = data_utils.rand_name('test-snap-')
        test_uuid = ('a' * 35)
        self.assertRaises(exceptions.NotFound,
                          self.servers_client.create_image,
                          test_uuid, snapshot_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_image_specify_uuid_37_characters_or_more(self):
        # Return an error if Image ID passed is 37 characters or more
        snapshot_name = data_utils.rand_name('test-snap-')
        test_uuid = ('a' * 37)
        self.assertRaises(exceptions.NotFound,
                          self.servers_client.create_image,
                          test_uuid, snapshot_name)
