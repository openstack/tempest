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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest import test

CONF = config.CONF


class ImagesOneServerTestJSON(base.BaseV2ComputeTest):

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
        cls.client = cls.compute_images_client

    def _get_default_flavor_disk_size(self, flavor_id):
        flavor = self.flavors_client.show_flavor(flavor_id)['flavor']
        return flavor['disk']

    @test.idempotent_id('3731d080-d4c5-4872-b41a-64d0d0021314')
    def test_create_delete_image(self):
        server_id = self.create_test_server(wait_until='ACTIVE')['id']

        # Create a new image
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        body = self.client.create_image(server_id, name=name,
                                        metadata=meta)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_image, image_id)
        waiters.wait_for_image_status(self.client, image_id, 'ACTIVE')

        # Verify the image was created correctly
        image = self.client.show_image(image_id)['image']
        self.assertEqual(name, image['name'])
        self.assertEqual('test', image['metadata']['image_type'])

        original_image = self.client.show_image(self.image_ref)['image']

        # Verify minRAM is the same as the original image
        self.assertEqual(image['minRam'], original_image['minRam'])

        # Verify minDisk is the same as the original image or the flavor size
        flavor_disk_size = self._get_default_flavor_disk_size(self.flavor_ref)
        self.assertIn(str(image['minDisk']),
                      (str(original_image['minDisk']), str(flavor_disk_size)))

        # Verify the image was deleted correctly
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

    @test.idempotent_id('3b7c6fe4-dfe7-477c-9243-b06359db51e6')
    def test_create_image_specify_multibyte_character_image_name(self):
        server_id = self.create_test_server(wait_until='ACTIVE')['id']

        # prefix character is:
        # http://www.fileformat.info/info/unicode/char/1F4A9/index.htm

        # We use a string with 3 byte utf-8 character due to bug
        # #1370954 in glance which will 500 if mysql is used as the
        # backend and it attempts to store a 4 byte utf-8 character
        utf8_name = data_utils.rand_name('\xe2\x82\xa1')
        body = self.client.create_image(server_id, name=utf8_name)
        image_id = data_utils.parse_image_id(body.response['location'])
        self.addCleanup(self.client.delete_image, image_id)
