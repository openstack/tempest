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
from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ImagesOneServerTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def resource_setup(cls):
        super(ImagesOneServerTestJSON, cls).resource_setup()
        cls.server_id = cls.create_test_server(wait_until='ACTIVE')['id']

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
        if cls.is_requested_microversion_compatible('2.35'):
            cls.client = cls.compute_images_client
        else:
            cls.client = cls.images_client

    def _get_default_flavor_disk_size(self, flavor_id):
        flavor = self.flavors_client.show_flavor(flavor_id)['flavor']
        return flavor['disk']

    @decorators.idempotent_id('3731d080-d4c5-4872-b41a-64d0d0021314')
    def test_create_delete_image(self):
        if self.is_requested_microversion_compatible('2.35'):
            MIN_DISK = 'minDisk'
            MIN_RAM = 'minRam'
        else:
            MIN_DISK = 'min_disk'
            MIN_RAM = 'min_ram'

        # Create a new image
        name = data_utils.rand_name('image')
        meta = {'image_type': 'test'}
        image = self.create_image_from_server(self.server_id, name=name,
                                              metadata=meta,
                                              wait_until='ACTIVE')

        # Verify the image was created correctly
        self.assertEqual(name, image['name'])
        if self.is_requested_microversion_compatible('2.35'):
            self.assertEqual('test', image['metadata']['image_type'])
        else:
            self.assertEqual('test', image['image_type'])

        original_image = self.client.show_image(self.image_ref)
        if self.is_requested_microversion_compatible('2.35'):
            original_image = original_image['image']

        # Verify minRAM is the same as the original image
        self.assertEqual(image[MIN_RAM], original_image[MIN_RAM])

        # Verify minDisk is the same as the original image or the flavor size
        flavor_disk_size = self._get_default_flavor_disk_size(self.flavor_ref)
        self.assertIn(str(image[MIN_DISK]),
                      (str(original_image[MIN_DISK]), str(flavor_disk_size)))

        # Verify the image was deleted correctly
        self.client.delete_image(image['id'])
        self.client.wait_for_resource_deletion(image['id'])

    @decorators.idempotent_id('3b7c6fe4-dfe7-477c-9243-b06359db51e6')
    def test_create_image_specify_multibyte_character_image_name(self):
        # prefix character is:
        # http://unicode.org/cldr/utility/character.jsp?a=20A1

        # We use a string with 3 byte utf-8 character due to nova/glance which
        # will return 400(Bad Request) if we attempt to send a name which has
        # 4 byte utf-8 character.
        utf8_name = data_utils.rand_name(b'\xe2\x82\xa1'.decode('utf-8'))
        body = self.compute_images_client.create_image(
            self.server_id, name=utf8_name)
        if api_version_utils.compare_version_header_to_response(
            "OpenStack-API-Version", "compute 2.45", body.response, "lt"):
            image_id = body['image_id']
        else:
            image_id = data_utils.parse_image_id(body.response['location'])
        self.addCleanup(self.client.delete_image, image_id)
