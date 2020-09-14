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

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF

LOG = logging.getLogger(__name__)


class ImagesOneServerNegativeTestJSON(base.BaseV2ComputeTest):
    """Negative tests of server images"""

    create_default_network = True

    def tearDown(self):
        """Terminate test instances created after a test is executed."""
        super(ImagesOneServerNegativeTestJSON, self).tearDown()
        # NOTE(zhufl): Because server_check_teardown will raise Exception
        # which will prevent other cleanup steps from being executed, so
        # server_check_teardown should be called after super's tearDown.
        self.server_check_teardown()

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ImagesOneServerNegativeTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            waiters.wait_for_server_status(self.servers_client, self.server_id,
                                           'ACTIVE')
        except Exception:
            LOG.exception('server %s timed out to become ACTIVE. rebuilding',
                          self.server_id)
            # Rebuild server if cannot reach the ACTIVE state
            # Usually it means the server had a serious accident
            self._reset_server()

    def _reset_server(self):
        self.__class__.server_id = self.recreate_server(self.server_id)

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
        if cls.is_requested_microversion_compatible('2.35'):
            cls.client = cls.compute_images_client
        else:
            cls.client = cls.images_client

    @classmethod
    def resource_setup(cls):
        super(ImagesOneServerNegativeTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('55d1d38c-dd66-4933-9c8e-7d92aeb60ddc')
    def test_create_image_specify_invalid_metadata(self):
        """Test creating server image with invalid metadata should fail"""
        meta = {'': ''}
        self.assertRaises(lib_exc.BadRequest, self.create_image_from_server,
                          self.server_id, metadata=meta)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3d24d11f-5366-4536-bd28-cff32b748eca')
    def test_create_image_specify_metadata_over_limits(self):
        """Test creating server image with metadata over 255 should fail"""
        meta = {'a' * 256: 'b' * 256}
        self.assertRaises(lib_exc.BadRequest, self.create_image_from_server,
                          self.server_id, metadata=meta)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0460efcf-ee88-4f94-acef-1bf658695456')
    def test_create_second_image_when_first_image_is_being_saved(self):
        """Test creating another server image when first image is being saved

        Creating another server image when first image is being saved is
        not allowed.
        """
        # Create first snapshot
        image = self.create_image_from_server(self.server_id)
        self.addCleanup(self._reset_server)

        # Create second snapshot
        self.assertRaises(lib_exc.Conflict, self.create_image_from_server,
                          self.server_id)

        if api_version_utils.compare_version_header_to_response(
            "OpenStack-API-Version", "compute 2.45", image.response, "lt"):
            image_id = image['image_id']
        else:
            image_id = data_utils.parse_image_id(image.response['location'])
        self.client.delete_image(image_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('084f0cbc-500a-4963-8a4e-312905862581')
    def test_create_image_specify_name_over_character_limit(self):
        """Test creating server image with image name over 255 should fail"""
        snapshot_name = ('a' * 256)
        self.assertRaises(lib_exc.BadRequest,
                          self.compute_images_client.create_image,
                          self.server_id, name=snapshot_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0894954d-2db2-4195-a45b-ffec0bc0187e')
    def test_delete_image_that_is_not_yet_active(self):
        """Test deleting a non-active server image should fail"""
        image = self.create_image_from_server(self.server_id)
        if api_version_utils.compare_version_header_to_response(
            "OpenStack-API-Version", "compute 2.45", image.response, "lt"):
            image_id = image['image_id']
        else:
            image_id = data_utils.parse_image_id(image.response['location'])

        self.addCleanup(self._reset_server)

        # Do not wait, attempt to delete the image, ensure it's successful
        self.client.delete_image(image_id)
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_image, image_id)
