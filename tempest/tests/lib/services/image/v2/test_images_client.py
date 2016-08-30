# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.image.v2 import images_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestImagesClient(base.BaseServiceTest):
    FAKE_CREATE_UPDATE_SHOW_IMAGE = {
        "id": "e485aab9-0907-4973-921c-bb6da8a8fcf8",
        "name": u"\u2740(*\xb4\u25e2`*)\u2740",
        "status": "active",
        "visibility": "public",
        "size": 2254249,
        "checksum": "2cec138d7dae2aa59038ef8c9aec2390",
        "tags": [
            "fedora",
            "beefy"
        ],
        "created_at": "2012-08-10T19:23:50Z",
        "updated_at": "2012-08-12T11:11:33Z",
        "self": "/v2/images/da3b75d9-3f4a-40e7-8a2c-bfab23927dea",
        "file": "/v2/images/da3b75d9-3f4a-40e7-8a2c-bfab23927dea/file",
        "schema": "/v2/schemas/image",
        "owner": None,
        "min_ram": None,
        "min_disk": None,
        "disk_format": None,
        "virtual_size": None,
        "container_format": None
    }

    def setUp(self):
        super(TestImagesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = images_client.ImagesClient(fake_auth,
                                                 'image', 'regionOne')

    def _test_update_image(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_image,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_CREATE_UPDATE_SHOW_IMAGE,
            bytes_body,
            image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8",
            patch=[{"op": "add", "path": "/a/b/c", "value": ["foo", "bar"]}])

    def _test_create_image(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_image,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_UPDATE_SHOW_IMAGE,
            bytes_body,
            name="virtual machine image",
            status=201)

    def _test_show_image(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_image,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CREATE_UPDATE_SHOW_IMAGE,
            bytes_body,
            image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8")

    def test_create_image_with_str_body(self):
        self._test_create_image()

    def test_create_image_with_bytes_body(self):
        self._test_create_image(bytes_body=True)

    def test_update_image_with_str_body(self):
        self._test_update_image()

    def test_update_image_with_bytes_body(self):
        self._test_update_image(bytes_body=True)

    def test_deactivate_image(self):
        self.check_service_client_function(
            self.client.deactivate_image,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8", status=204)

    def test_reactivate_image(self):
        self.check_service_client_function(
            self.client.reactivate_image,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8", status=204)

    def test_delete_image(self):
        self.check_service_client_function(
            self.client.delete_image,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, image_id="e485aab9-0907-4973-921c-bb6da8a8fcf8", status=204)

    def test_show_image_with_str_body(self):
        self._test_show_image()

    def test_show_image_with_bytes_body(self):
        self._test_show_image(bytes_body=True)
