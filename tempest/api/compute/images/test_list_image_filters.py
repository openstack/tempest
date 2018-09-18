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

import time

import six
import testtools

from tempest.api.compute import base
from tempest.common import image as common_image
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class ListImageFiltersTestJSON(base.BaseV2ComputeTest):
    max_microversion = '2.35'

    @classmethod
    def skip_checks(cls):
        super(ListImageFiltersTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ListImageFiltersTestJSON, cls).setup_clients()
        cls.client = cls.compute_images_client
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

    @classmethod
    def resource_setup(cls):
        super(ListImageFiltersTestJSON, cls).resource_setup()

        def _create_image():
            params = {
                'name': data_utils.rand_name(cls.__name__ + '-image'),
                'container_format': 'bare',
                'disk_format': 'raw'
            }
            if CONF.image_feature_enabled.api_v1:
                params.update({'is_public': False})
                params = {'headers':
                          common_image.image_meta_to_headers(**params)}
            else:
                params.update({'visibility': 'private'})

            body = cls.glance_client.create_image(**params)
            body = body['image'] if 'image' in body else body
            image_id = body['id']
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                cls.compute_images_client.delete_image,
                image_id)
            # Wait 1 second between creation and upload to ensure a delta
            # between created_at and updated_at.
            time.sleep(1)
            image_file = six.BytesIO((b'*' * 1024))
            if CONF.image_feature_enabled.api_v1:
                cls.glance_client.update_image(image_id, data=image_file)
            else:
                cls.glance_client.store_image_file(image_id, data=image_file)
            waiters.wait_for_image_status(cls.client, image_id, 'ACTIVE')
            body = cls.client.show_image(image_id)['image']
            return body

        # Create non-snapshot images via glance
        cls.image1 = _create_image()
        cls.image1_id = cls.image1['id']
        cls.image2 = _create_image()
        cls.image2_id = cls.image2['id']
        cls.image3 = _create_image()
        cls.image3_id = cls.image3['id']

        if not CONF.compute_feature_enabled.snapshot:
            return

        # Create instances and snapshots via nova
        cls.server1 = cls.create_test_server()
        cls.server2 = cls.create_test_server(wait_until='ACTIVE')
        # NOTE(sdague) this is faster than doing the sync wait_util on both
        waiters.wait_for_server_status(cls.servers_client,
                                       cls.server1['id'], 'ACTIVE')

        # Create images to be used in the filter tests
        cls.snapshot1 = cls.create_image_from_server(
            cls.server1['id'], wait_until='ACTIVE')
        cls.snapshot1_id = cls.snapshot1['id']

        # Servers have a hidden property for when they are being imaged
        # Performing back-to-back create image calls on a single
        # server will sometimes cause failures
        cls.snapshot3 = cls.create_image_from_server(
            cls.server2['id'], wait_until='ACTIVE')
        cls.snapshot3_id = cls.snapshot3['id']

        # Wait for the server to be active after the image upload
        cls.snapshot2 = cls.create_image_from_server(
            cls.server1['id'], wait_until='ACTIVE')
        cls.snapshot2_id = cls.snapshot2['id']

    @decorators.idempotent_id('a3f5b513-aeb3-42a9-b18e-f091ef73254d')
    def test_list_images_filter_by_status(self):
        # The list of images should contain only images with the
        # provided status
        params = {'status': 'ACTIVE'}
        images = self.client.list_images(**params)['images']

        self.assertNotEmpty([i for i in images if i['id'] == self.image1_id])
        self.assertNotEmpty([i for i in images if i['id'] == self.image2_id])
        self.assertNotEmpty([i for i in images if i['id'] == self.image3_id])

    @decorators.idempotent_id('33163b73-79f5-4d07-a7ea-9213bcc468ff')
    def test_list_images_filter_by_name(self):
        # List of all images should contain the expected images filtered
        # by name
        params = {'name': self.image1['name']}
        images = self.client.list_images(**params)['images']

        self.assertNotEmpty([i for i in images if i['id'] == self.image1_id])
        self.assertEmpty([i for i in images if i['id'] == self.image2_id])
        self.assertEmpty([i for i in images if i['id'] == self.image3_id])

    @decorators.idempotent_id('9f238683-c763-45aa-b848-232ec3ce3105')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    def test_list_images_filter_by_server_id(self):
        # The images should contain images filtered by server id
        params = {'server': self.server1['id']}
        images = self.client.list_images(**params)['images']

        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot1_id],
                            "Failed to find image %s in images. "
                            "Got images %s" % (self.image1_id, images))
        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot2_id])
        self.assertEmpty([i for i in images if i['id'] == self.snapshot3_id])

    @decorators.idempotent_id('05a377b8-28cf-4734-a1e6-2ab5c38bf606')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    def test_list_images_filter_by_server_ref(self):
        # The list of servers should be filtered by server ref
        server_links = self.server2['links']

        # Try all server link types
        for link in server_links:
            params = {'server': link['href']}
            images = self.client.list_images(**params)['images']

            self.assertEmpty([i for i in images
                              if i['id'] == self.snapshot1_id])
            self.assertEmpty([i for i in images
                              if i['id'] == self.snapshot2_id])
            self.assertNotEmpty([i for i in images
                                 if i['id'] == self.snapshot3_id])

    @decorators.idempotent_id('e3356918-4d3e-4756-81d5-abc4524ba29f')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    def test_list_images_filter_by_type(self):
        # The list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        images = self.client.list_images(**params)['images']

        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot1_id])
        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot2_id])
        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot3_id])
        self.assertEmpty([i for i in images if i['id'] == self.image_ref])

    @decorators.idempotent_id('3a484ca9-67ba-451e-b494-7fcf28d32d62')
    def test_list_images_limit_results(self):
        # Verify only the expected number of results are returned
        params = {'limit': '1'}
        images = self.client.list_images(**params)['images']
        self.assertEqual(1, len([x for x in images if 'id' in x]))

    @decorators.idempotent_id('18bac3ae-da27-436c-92a9-b22474d13aab')
    def test_list_images_filter_by_changes_since(self):
        # Verify only updated images are returned in the detailed list

        # Becoming ACTIVE will modify the updated time
        # Filter by the image's created time
        params = {'changes-since': self.image3['created']}
        images = self.client.list_images(**params)['images']
        found = [i for i in images if i['id'] == self.image3_id]
        self.assertNotEmpty(found)

    @decorators.idempotent_id('9b0ea018-6185-4f71-948a-a123a107988e')
    def test_list_images_with_detail_filter_by_status(self):
        # Detailed list of all images should only contain images
        # with the provided status
        params = {'status': 'ACTIVE'}
        images = self.client.list_images(detail=True, **params)['images']

        self.assertNotEmpty([i for i in images if i['id'] == self.image1_id])
        self.assertNotEmpty([i for i in images if i['id'] == self.image2_id])
        self.assertNotEmpty([i for i in images if i['id'] == self.image3_id])

    @decorators.idempotent_id('644ea267-9bd9-4f3b-af9f-dffa02396a17')
    def test_list_images_with_detail_filter_by_name(self):
        # Detailed list of all images should contain the expected
        # images filtered by name
        params = {'name': self.image1['name']}
        images = self.client.list_images(detail=True, **params)['images']

        self.assertNotEmpty([i for i in images if i['id'] == self.image1_id])
        self.assertEmpty([i for i in images if i['id'] == self.image2_id])
        self.assertEmpty([i for i in images if i['id'] == self.image3_id])

    @decorators.idempotent_id('ba2fa9a9-b672-47cc-b354-3b4c0600e2cb')
    def test_list_images_with_detail_limit_results(self):
        # Verify only the expected number of results (with full details)
        # are returned
        params = {'limit': '1'}
        images = self.client.list_images(detail=True, **params)['images']
        self.assertEqual(1, len(images))

    @decorators.idempotent_id('8c78f822-203b-4bf6-8bba-56ebd551cf84')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    def test_list_images_with_detail_filter_by_server_ref(self):
        # Detailed list of servers should be filtered by server ref
        server_links = self.server2['links']

        # Try all server link types
        for link in server_links:
            params = {'server': link['href']}
            images = self.client.list_images(detail=True, **params)['images']

            self.assertEmpty([i for i in images
                              if i['id'] == self.snapshot1_id])
            self.assertEmpty([i for i in images
                              if i['id'] == self.snapshot2_id])
            self.assertNotEmpty([i for i in images
                                 if i['id'] == self.snapshot3_id])

    @decorators.idempotent_id('888c0cc0-7223-43c5-9db0-b125fd0a393b')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    def test_list_images_with_detail_filter_by_type(self):
        # The detailed list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        images = self.client.list_images(detail=True, **params)['images']
        self.client.show_image(self.image_ref)

        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot1_id])
        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot2_id])
        self.assertNotEmpty([i for i in images
                             if i['id'] == self.snapshot3_id])
        self.assertEmpty([i for i in images if i['id'] == self.image_ref])

    @decorators.idempotent_id('7d439e18-ac2e-4827-b049-7e18004712c4')
    def test_list_images_with_detail_filter_by_changes_since(self):
        # Verify an update image is returned

        # Becoming ACTIVE will modify the updated time
        # Filter by the image's created time
        params = {'changes-since': self.image1['created']}
        images = self.client.list_images(detail=True, **params)['images']
        self.assertNotEmpty([i for i in images if i['id'] == self.image1_id])
