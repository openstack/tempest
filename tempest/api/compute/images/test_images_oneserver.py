# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ImagesOneServerTestJSON(base.BaseV2ComputeTest):

    def tearDown(self):
        """Terminate test instances created after a test is executed."""
        self.server_check_teardown()
        super(ImagesOneServerTestJSON, self).tearDown()

    def setUp(self):
        # NOTE(afazekas): Normally we use the same server with all test cases,
        # but if it has an issue, we build a new one
        super(ImagesOneServerTestJSON, self).setUp()
        # Check if the server is in a clean state after test
        try:
            self.servers_client.wait_for_server_status(self.server_id,
                                                       'ACTIVE')
        except Exception:
            LOG.exception('server %s timed out to become ACTIVE. rebuilding'
                          % self.server_id)
            # Rebuild server if cannot reach the ACTIVE state
            # Usually it means the server had a serious accident
            self.__class__.server_id = self.rebuild_server(self.server_id)

    @classmethod
    def skip_checks(cls):
        super(ImagesOneServerTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        if not CONF.compute_feature_enabled.snapshot:
            skip_msg = ("%s skipped as instance snapshotting is not supported"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesOneServerTestJSON, cls).setup_clients()
        cls.client = cls.images_client

    @classmethod
    def resource_setup(cls):
        super(ImagesOneServerTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    def _get_default_flavor_disk_size(self, flavor_id):
        flavor = self.flavors_client.get_flavor_details(flavor_id)
        return flavor['disk']

    @test.attr(type='smoke')
    @test.idempotent_id('3731d080-d4c5-4872-b41a-64d0d0021314')
    def test_create_delete_image(self):

        # Create a new image
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        body = self.client.create_image(self.server_id, name, meta)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        # Verify the image was created correctly
        image = self.client.get_image(image_id)
        self.assertEqual(name, image['name'])
        self.assertEqual('test', image['metadata']['image_type'])

        original_image = self.client.get_image(self.image_ref)

        # Verify minRAM is the same as the original image
        self.assertEqual(image['minRam'], original_image['minRam'])

        # Verify minDisk is the same as the original image or the flavor size
        flavor_disk_size = self._get_default_flavor_disk_size(self.flavor_ref)
        self.assertIn(str(image['minDisk']),
                      (str(original_image['minDisk']), str(flavor_disk_size)))

        # Verify the image was deleted correctly
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

    @test.attr(type=['gate'])
    @test.idempotent_id('3b7c6fe4-dfe7-477c-9243-b06359db51e6')
    def test_create_image_specify_multibyte_character_image_name(self):
        # prefix character is:
        # http://www.fileformat.info/info/unicode/char/1F4A9/index.htm

        # We use a string with 3 byte utf-8 character due to bug
        # #1370954 in glance which will 500 if mysql is used as the
        # backend and it attempts to store a 4 byte utf-8 character
        utf8_name = data_utils.rand_name('\xe2\x82\xa1')
        body = self.client.create_image(self.server_id, utf8_name)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.addCleanup(self.client.delete_image, image_id)
