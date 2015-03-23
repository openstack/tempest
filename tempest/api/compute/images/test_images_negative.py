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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class ImagesNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ImagesNegativeTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.compute_feature_enabled.snapshot:
            skip_msg = ("%s skipped as instance snapshotting is not supported"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesNegativeTestJSON, cls).setup_clients()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6cd5a89d-5b47-46a7-93bc-3916f0d84973')
    def test_create_image_from_deleted_server(self):
        # An image should not be created if the server instance is removed
        server = self.create_test_server(wait_until='ACTIVE')

        # Delete server before trying to create server
        self.servers_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])
        # Create a new image after server is deleted
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        self.assertRaises(lib_exc.NotFound,
                          self.create_image_from_server,
                          server['id'], name=name, meta=meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('82c5b0c4-9dbd-463c-872b-20c4755aae7f')
    def test_create_image_from_invalid_server(self):
        # An image should not be created with invalid server id
        # Create a new image with invalid server id
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        resp = {}
        resp['status'] = None
        self.assertRaises(lib_exc.NotFound, self.create_image_from_server,
                          '!@#$%^&*()', name=name, meta=meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('aaacd1d0-55a2-4ce8-818a-b5439df8adc9')
    def test_create_image_from_stopped_server(self):
        server = self.create_test_server(wait_until='ACTIVE')
        self.servers_client.stop(server['id'])
        self.servers_client.wait_for_server_status(server['id'],
                                                   'SHUTOFF')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        snapshot_name = data_utils.rand_name('test-snap')
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='ACTIVE',
                                              wait_for_server=False)
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertEqual(snapshot_name, image['name'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ec176029-73dc-4037-8d72-2e4ff60cf538')
    def test_create_image_specify_uuid_35_characters_or_less(self):
        # Return an error if Image ID passed is 35 characters or less
        snapshot_name = data_utils.rand_name('test-snap')
        test_uuid = ('a' * 35)
        self.assertRaises(lib_exc.NotFound, self.client.create_image,
                          test_uuid, snapshot_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('36741560-510e-4cc2-8641-55fe4dfb2437')
    def test_create_image_specify_uuid_37_characters_or_more(self):
        # Return an error if Image ID passed is 37 characters or more
        snapshot_name = data_utils.rand_name('test-snap')
        test_uuid = ('a' * 37)
        self.assertRaises(lib_exc.NotFound, self.client.create_image,
                          test_uuid, snapshot_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('381acb65-785a-4942-94ce-d8f8c84f1f0f')
    def test_delete_image_with_invalid_image_id(self):
        # An image should not be deleted with invalid image id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          '!@$%^&*()')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('137aef61-39f7-44a1-8ddf-0adf82511701')
    def test_delete_non_existent_image(self):
        # Return an error while trying to delete a non-existent image

        non_existent_image_id = '11a22b9-12a9-5555-cc11-00ab112223fa'
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e6e41425-af5c-4fe6-a4b5-7b7b963ffda5')
    def test_delete_image_blank_id(self):
        # Return an error while trying to delete an image with blank Id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image, '')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('924540c3-f1f1-444c-8f58-718958b6724e')
    def test_delete_image_non_hex_string_id(self):
        # Return an error while trying to delete an image with non hex id
        image_id = '11a22b9-120q-5555-cc11-00ab112223gj'
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('68e2c175-bd26-4407-ac0f-4ea9ce2139ea')
    def test_delete_image_negative_image_id(self):
        # Return an error while trying to delete an image with negative id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image, -1)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('b340030d-82cd-4066-a314-c72fb7c59277')
    def test_delete_image_id_is_over_35_character_limit(self):
        # Return an error while trying to delete image with id over limit
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          '11a22b9-12a9-5555-cc11-00ab112223fa-3fac')
