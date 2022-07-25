# Copyright 2022 Red Hat, Inc.  All rights reserved.
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

from tempest.lib.services.image.v2 import image_cache_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestImageCacheClient(base.BaseServiceTest):
    def setUp(self):
        super(TestImageCacheClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = image_cache_client.ImageCacheClient(
            fake_auth, 'image', 'regionOne')

    def test_list_cache(self):
        fake_result = {
            "cached_images": [{
                "image_id": "8f332e84-ea60-4501-8e11-5efcddb81f30",
                "hits": 3,
                "last_accessed": 1639578364.65118,
                "last_modified": 1639389612.596718,
                "size": 16300544
            }],
            "queued_images": ['1bea47ed-f6a9-463b-b423-14b9cca9ad27']}
        self.check_service_client_function(
            self.client.list_cache,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_result,
            mock_args=['cache'])

    def test_cache_queue(self):
        self.check_service_client_function(
            self.client.cache_queue,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            status=202,
            image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8")

    def test_cache_delete(self):
        fake_result = {}
        self.check_service_client_function(
            self.client.cache_delete,
            'tempest.lib.common.rest_client.RestClient.delete',
            fake_result, image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8",
            status=204)

    def test_cache_clear_without_target(self):
        fake_result = {}
        self.check_service_client_function(
            self.client.cache_clear,
            'tempest.lib.common.rest_client.RestClient.delete',
            fake_result, status=204)
