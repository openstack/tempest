# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class ImagesOneServerNegativeTestJSON(base.BaseV2ComputeTest):

    def tearDown(self):
        """Terminate test instances created after a test is executed."""
        for image_id in self.image_ids:
            self.client.delete_image(image_id)
            self.image_ids.remove(image_id)
        self.server_check_teardown()
        super(ImagesOneServerNegativeTestJSON, self).tearDown()

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ImagesOneServerNegativeTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            self.servers_client.wait_for_server_status(self.server_id,
                                                       'ACTIVE')
        except Exception:
            LOG.exception('server %s timed out to become ACTIVE. rebuilding'
                          % self.server_id)
            # Rebuild server if cannot reach the ACTIVE state
            # Usually it means the server had a serious accident
            self._reset_server()

    def _reset_server(self):
        self.__class__.server_id = self.rebuild_server(self.server_id)

    @classmethod
    def skip_checks(cls):
        super(ImagesOneServerNegativeTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        if not CONF.compute_feature_enabled.snapshot:
            skip_msg = ("%s skipped as instance snapshotting is not supported"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesOneServerNegativeTestJSON, cls).setup_clients()
        cls.client = cls.images_client

    @classmethod
    def resource_setup(cls):
        super(ImagesOneServerNegativeTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

        cls.image_ids = []

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('55d1d38c-dd66-4933-9c8e-7d92aeb60ddc')
    def test_create_image_specify_invalid_metadata(self):
        # Return an error when creating image with invalid metadata
        snapshot_name = data_utils.rand_name('test-snap')
        meta = {'': ''}
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          self.server_id, snapshot_name, meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('3d24d11f-5366-4536-bd28-cff32b748eca')
    def test_create_image_specify_metadata_over_limits(self):
        # Return an error when creating image with meta data over 256 chars
        snapshot_name = data_utils.rand_name('test-snap')
        meta = {'a' * 260: 'b' * 260}
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          self.server_id, snapshot_name, meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0460efcf-ee88-4f94-acef-1bf658695456')
    def test_create_second_image_when_first_image_is_being_saved(self):
        # Disallow creating another image when first image is being saved

        # Create first snapshot
        snapshot_name = data_utils.rand_name('test-snap')
        body = self.client.create_image(self.server_id,
                                        snapshot_name)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.image_ids.append(image_id)
        self.addCleanup(self._reset_server)

        # Create second snapshot
        alt_snapshot_name = data_utils.rand_name('test-snap')
        self.assertRaises(lib_exc.Conflict, self.client.create_image,
                          self.server_id, alt_snapshot_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('084f0cbc-500a-4963-8a4e-312905862581')
    def test_create_image_specify_name_over_256_chars(self):
        # Return an error if snapshot name over 256 characters is passed

        snapshot_name = data_utils.rand_name('a' * 260)
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          self.server_id, snapshot_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0894954d-2db2-4195-a45b-ffec0bc0187e')
    def test_delete_image_that_is_not_yet_active(self):
        # Return an error while trying to delete an image what is creating

        snapshot_name = data_utils.rand_name('test-snap')
        body = self.client.create_image(self.server_id, snapshot_name)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.image_ids.append(image_id)
        self.addCleanup(self._reset_server)

        # Do not wait, attempt to delete the image, ensure it's successful
        self.client.delete_image(image_id)
        self.image_ids.remove(image_id)

        self.assertRaises(lib_exc.NotFound, self.client.get_image, image_id)
