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

import six

from tempest.api.compute import base
from tempest.common import image as common_image
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class ImagesMetadataTestJSON(base.BaseV2ComputeTest):
    max_microversion = '2.38'

    @classmethod
    def skip_checks(cls):
        super(ImagesMetadataTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesMetadataTestJSON, cls).setup_clients()
        # Check if glance v1 is available to determine which client to use. We
        # prefer glance v1 for the compute API tests since the compute image
        # API proxy was written for glance v1.
        if CONF.image_feature_enabled.api_v1:
            cls.glance_client = cls.os_primary.image_client
        elif CONF.image_feature_enabled.api_v2:
            cls.glance_client = cls.os_primary.image_client_v2
        else:
            raise exceptions.InvalidConfiguration(
                'Either api_v1 or api_v2 must be True in '
                '[image-feature-enabled].')
        cls.client = cls.compute_images_client

    @classmethod
    def resource_setup(cls):
        super(ImagesMetadataTestJSON, cls).resource_setup()
        cls.image_id = None

        params = {
            'name': data_utils.rand_name('image'),
            'container_format': 'bare',
            'disk_format': 'raw'
        }
        if CONF.image_feature_enabled.api_v1:
            params.update({'is_public': False})
            params = {'headers': common_image.image_meta_to_headers(**params)}
        else:
            params.update({'visibility': 'private'})

        body = cls.glance_client.create_image(**params)
        body = body['image'] if 'image' in body else body
        cls.image_id = body['id']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.glance_client.delete_image,
                                    cls.image_id)
        image_file = six.BytesIO((b'*' * 1024))
        if CONF.image_feature_enabled.api_v1:
            cls.glance_client.update_image(cls.image_id, data=image_file)
        else:
            cls.glance_client.store_image_file(cls.image_id, data=image_file)
        waiters.wait_for_image_status(cls.client, cls.image_id, 'ACTIVE')

    def setUp(self):
        super(ImagesMetadataTestJSON, self).setUp()
        meta = {'os_version': 'value1', 'os_distro': 'value2'}
        self.client.set_image_metadata(self.image_id, meta)

    @decorators.idempotent_id('37ec6edd-cf30-4c53-bd45-ae74db6b0531')
    def test_list_image_metadata(self):
        # All metadata key/value pairs for an image should be returned
        resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'metadata': {
            'os_version': 'value1', 'os_distro': 'value2'}}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('ece7befc-d3ce-42a4-b4be-c3067a418c29')
    def test_set_image_metadata(self):
        # The metadata for the image should match the new values
        req_metadata = {'os_version': 'value2', 'architecture': 'value3'}
        self.client.set_image_metadata(self.image_id,
                                       req_metadata)

        resp_metadata = (self.client.list_image_metadata(self.image_id)
                         ['metadata'])
        self.assertEqual(req_metadata, resp_metadata)

    @decorators.idempotent_id('7b491c11-a9d5-40fe-a696-7f7e03d3fea2')
    def test_update_image_metadata(self):
        # The metadata for the image should match the updated values
        req_metadata = {'os_version': 'alt1', 'architecture': 'value3'}
        self.client.update_image_metadata(self.image_id,
                                          req_metadata)

        resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'metadata': {
            'os_version': 'alt1',
            'os_distro': 'value2',
            'architecture': 'value3'}}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('4f5db52f-6685-4c75-b848-f4bb363f9aa6')
    def test_get_image_metadata_item(self):
        # The value for a specific metadata key should be returned
        meta = self.client.show_image_metadata_item(self.image_id,
                                                    'os_distro')['meta']
        self.assertEqual('value2', meta['os_distro'])

    @decorators.idempotent_id('f2de776a-4778-4d90-a5da-aae63aee64ae')
    def test_set_image_metadata_item(self):
        # The value provided for the given meta item should be set for
        # the image
        meta = {'os_version': 'alt'}
        self.client.set_image_metadata_item(self.image_id,
                                            'os_version', meta)
        resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'metadata': {'os_version': 'alt', 'os_distro': 'value2'}}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('a013796c-ba37-4bb5-8602-d944511def14')
    def test_delete_image_metadata_item(self):
        # The metadata value/key pair should be deleted from the image
        self.client.delete_image_metadata_item(self.image_id,
                                               'os_version')
        resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'metadata': {'os_distro': 'value2'}}
        self.assertEqual(expected, resp_metadata)
