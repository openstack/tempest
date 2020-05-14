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

import six

from tempest.lib.common.utils import data_utils
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
        "file": "/v2/images/da3b75d9-3f4a-40e7-8a2c-bfab23927"
                "dea/file",
        "schema": "/v2/schemas/image",
        "owner": None,
        "min_ram": None,
        "min_disk": None,
        "disk_format": None,
        "virtual_size": None,
        "container_format": None,
        "os_hash_algo": "sha512",
        "os_hash_value": "ef7d1ed957ffafefb324d50ebc6685ed03d0e645d",
        "os_hidden": False,
        "protected": False,
    }

    FAKE_LIST_IMAGES = {
        "images": [
            {
                "status": "active",
                "name": "cirros-0.3.2-x86_64-disk",
                "tags": [],
                "container_format": "bare",
                "created_at": "2014-11-07T17:07:06Z",
                "disk_format": "qcow2",
                "updated_at": "2014-11-07T17:19:09Z",
                "visibility": "public",
                "self": "/v2/images/1bea47ed-f6a9-463b-b423-14b9cca9ad27",
                "min_disk": 0,
                "protected": False,
                "id": "1bea47ed-f6a9-463b-b423-14b9cca9ad27",
                "file": "/v2/images/1bea47ed-f6a9-463b-b423-14b9cca9ad27/file",
                "checksum": "64d7c1cd2b6f60c92c14662941cb7913",
                "owner": "5ef70662f8b34079a6eddb8da9d75fe8",
                "size": 13167616,
                "min_ram": 0,
                "schema": "/v2/schemas/image",
                "virtual_size": None,
                "os_hash_algo": "sha512",
                "os_hash_value": "ef7d1ed957ffafefb324d50ebc6685ed03d0e645d",
                "os_hidden": False
            },
            {
                "status": "active",
                "name": "F17-x86_64-cfntools",
                "tags": [],
                "container_format": "bare",
                "created_at": "2014-10-30T08:23:39Z",
                "disk_format": "qcow2",
                "updated_at": "2014-11-03T16:40:10Z",
                "visibility": "public",
                "self": "/v2/images/781b3762-9469-4cec-b58d-3349e5de4e9c",
                "min_disk": 0,
                "protected": False,
                "id": "781b3762-9469-4cec-b58d-3349e5de4e9c",
                "file": "/v2/images/781b3762-9469-4cec-b58d-3349e5de4e9c/file",
                "checksum": "afab0f79bac770d61d24b4d0560b5f70",
                "owner": "5ef70662f8b34079a6eddb8da9d75fe8",
                "size": 476704768,
                "min_ram": 0,
                "schema": "/v2/schemas/image",
                "virtual_size": None,
                "os_hash_algo": "sha512",
                "os_hash_value": "ef7d1ed957ffafefb324d50ebc6685ed03d0e645d",
                "os_hidden": False
            }
        ],
        "schema": "/v2/schemas/images",
        "first": "/v2/images"
    }

    FAKE_TAG_NAME = "fake tag"

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

    def _test_list_images(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_images,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_IMAGES,
            bytes_body,
            mock_args=['images'])

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

    def test_store_image_file(self):
        data = six.BytesIO(data_utils.random_bytes())

        self.check_service_client_function(
            self.client.store_image_file,
            'tempest.lib.common.rest_client.RestClient.raw_request',
            {},
            image_id=self.FAKE_CREATE_UPDATE_SHOW_IMAGE["id"],
            status=204,
            data=data)

    def test_show_image_file(self):
        # NOTE: The response for this API returns raw binary data, but an error
        # is thrown if random bytes are used for the resp body since
        # ``create_response`` then calls ``json.dumps``.
        self.check_service_client_function(
            self.client.show_image_file,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            resp_as_string=True,
            image_id=self.FAKE_CREATE_UPDATE_SHOW_IMAGE["id"],
            headers={'Content-Type': 'application/octet-stream'},
            status=200)

    def test_add_image_tag(self):
        self.check_service_client_function(
            self.client.add_image_tag,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            image_id=self.FAKE_CREATE_UPDATE_SHOW_IMAGE["id"],
            status=204,
            tag=self.FAKE_TAG_NAME)

    def test_delete_image_tag(self):
        self.check_service_client_function(
            self.client.delete_image_tag,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            image_id=self.FAKE_CREATE_UPDATE_SHOW_IMAGE["id"],
            status=204,
            tag=self.FAKE_TAG_NAME)

    def test_show_image_with_str_body(self):
        self._test_show_image()

    def test_show_image_with_bytes_body(self):
        self._test_show_image(bytes_body=True)

    def test_list_images_with_str_body(self):
        self._test_list_images()

    def test_list_images_with_bytes_body(self):
        self._test_list_images(bytes_body=True)
