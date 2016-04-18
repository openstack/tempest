# Copyright 2015 NEC Corporation.  All rights reserved.
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

import copy

from oslotest import mockpatch

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import images_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestImagesClient(base.BaseComputeServiceTest):
    # Data Dictionaries used for testing #
    FAKE_IMAGE_METADATA = {
        "list":
            {"metadata": {
             "auto_disk_config": "True",
             "Label": "Changed"
             }},
        "set_item":
            {"meta": {
             "auto_disk_config": "True"
             }},
        "show_item":
            {"meta": {
             "kernel_id": "nokernel",
             }},
        "update":
            {"metadata": {
             "kernel_id": "False",
             "Label": "UpdatedImage"
             }},
        "set":
            {"metadata": {
             "Label": "Changed",
             "auto_disk_config": "True"
             }},
        "delete_item": {}
        }

    FAKE_IMAGE_DATA = {
        "list":
            {"images": [
             {"id": "70a599e0-31e7-49b7-b260-868f441e862b",
              "links": [
                    {"href": "http://openstack.example.com/v2/openstack" +
                             "/images/70a599e0-31e7-49b7-b260-868f441e862b",
                     "rel": "self"
                     }
              ],
              "name": "fakeimage7"
              }]},
        "show": {"image": {
            "created": "2011-01-01T01:02:03Z",
            "id": "70a599e0-31e7-49b7-b260-868f441e862b",
            "links": [
                {
                    "href": "http://openstack.example.com/v2/openstack" +
                            "/images/70a599e0-31e7-49b7-b260-868f441e862b",
                    "rel": "self"
                },
            ],
            "metadata": {
                "architecture": "x86_64",
                "auto_disk_config": "True",
                "kernel_id": "nokernel",
                "ramdisk_id": "nokernel"
            },
            "minDisk": 0,
            "minRam": 0,
            "name": "fakeimage7",
            "progress": 100,
            "status": "ACTIVE",
            "updated": "2011-01-01T01:02:03Z"}},
        "create": {},
        "delete": {}
        }
    func2mock = {
        'get': 'tempest.lib.common.rest_client.RestClient.get',
        'post': 'tempest.lib.common.rest_client.RestClient.post',
        'put': 'tempest.lib.common.rest_client.RestClient.put',
        'delete': 'tempest.lib.common.rest_client.RestClient.delete'}
    # Variable definition
    FAKE_IMAGE_ID = FAKE_IMAGE_DATA['show']['image']['id']
    FAKE_SERVER_ID = "80a599e0-31e7-49b7-b260-868f441e343f"
    FAKE_CREATE_INFO = {'location': 'None'}
    FAKE_METADATA = FAKE_IMAGE_METADATA['show_item']['meta']

    def setUp(self):
        super(TestImagesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = images_client.ImagesClient(fake_auth,
                                                 "compute", "regionOne")

    def _test_image_operation(self, operation="delete", bytes_body=False):
        response_code = 200
        mock_operation = self.func2mock['get']
        expected_op = self.FAKE_IMAGE_DATA[operation]
        params = {"image_id": self.FAKE_IMAGE_ID}
        headers = None
        if operation == 'list':
            function = self.client.list_images
        elif operation == 'show':
            function = self.client.show_image
        elif operation == 'create':
            function = self.client.create_image
            mock_operation = self.func2mock['post']
            params = {"server_id": self.FAKE_SERVER_ID}
            response_code = 202
            headers = {
                'connection': 'keep-alive',
                'content-length': '0',
                'content-type': 'application/json',
                'status': '202',
                'x-compute-request-id': 'req-fake',
                'vary': 'accept-encoding',
                'x-openstack-nova-api-version': 'v2.1',
                'date': '13 Oct 2015 05:55:36 GMT',
                'location': 'http://fake.com/images/fake'
            }
        else:
            function = self.client.delete_image
            mock_operation = self.func2mock['delete']
            response_code = 204

        self.check_service_client_function(
            function, mock_operation, expected_op,
            bytes_body, response_code, headers, **params)

    def _test_image_metadata(self, operation="set_item", bytes_body=False):
        response_code = 200
        expected_op = self.FAKE_IMAGE_METADATA[operation]
        if operation == 'list':
            function = self.client.list_image_metadata
            mock_operation = self.func2mock['get']
            params = {"image_id": self.FAKE_IMAGE_ID}

        elif operation == 'set':
            function = self.client.set_image_metadata
            mock_operation = self.func2mock['put']
            params = {"image_id": "_dummy_data",
                      "meta": self.FAKE_METADATA}

        elif operation == 'update':
            function = self.client.update_image_metadata
            mock_operation = self.func2mock['post']
            params = {"image_id": self.FAKE_IMAGE_ID,
                      "meta": self.FAKE_METADATA}

        elif operation == 'show_item':
            mock_operation = self.func2mock['get']
            function = self.client.show_image_metadata_item
            params = {"image_id": self.FAKE_IMAGE_ID,
                      "key": "123"}

        elif operation == 'delete_item':
            function = self.client.delete_image_metadata_item
            mock_operation = self.func2mock['delete']
            response_code = 204
            params = {"image_id": self.FAKE_IMAGE_ID,
                      "key": "123"}

        else:
            function = self.client.set_image_metadata_item
            mock_operation = self.func2mock['put']
            params = {"image_id": self.FAKE_IMAGE_ID,
                      "key": "123",
                      "meta": self.FAKE_METADATA}

        self.check_service_client_function(
            function, mock_operation, expected_op,
            bytes_body, response_code, **params)

    def _test_resource_deleted(self, bytes_body=False):
        params = {"id": self.FAKE_IMAGE_ID}
        expected_op = self.FAKE_IMAGE_DATA['show']
        self.useFixture(mockpatch.Patch('tempest.lib.services.compute'
                        '.images_client.ImagesClient.show_image',
                                        side_effect=lib_exc.NotFound))
        self.assertEqual(True, self.client.is_resource_deleted(**params))
        tempdata = copy.deepcopy(self.FAKE_IMAGE_DATA['show'])
        tempdata['image']['id'] = None
        self.useFixture(mockpatch.Patch('tempest.lib.services.compute'
                        '.images_client.ImagesClient.show_image',
                                        return_value=expected_op))
        self.assertEqual(False, self.client.is_resource_deleted(**params))

    def test_list_images_with_str_body(self):
        self._test_image_operation('list')

    def test_list_images_with_bytes_body(self):
        self._test_image_operation('list', True)

    def test_show_image_with_str_body(self):
        self._test_image_operation('show')

    def test_show_image_with_bytes_body(self):
        self._test_image_operation('show', True)

    def test_create_image_with_str_body(self):
        self._test_image_operation('create')

    def test_create_image_with_bytes_body(self):
        self._test_image_operation('create', True)

    def test_delete_image_with_str_body(self):
        self._test_image_operation('delete')

    def test_delete_image_with_bytes_body(self):
        self._test_image_operation('delete', True)

    def test_list_image_metadata_with_str_body(self):
        self._test_image_metadata('list')

    def test_list_image_metadata_with_bytes_body(self):
        self._test_image_metadata('list', True)

    def test_set_image_metadata_with_str_body(self):
        self._test_image_metadata('set')

    def test_set_image_metadata_with_bytes_body(self):
        self._test_image_metadata('set', True)

    def test_update_image_metadata_with_str_body(self):
        self._test_image_metadata('update')

    def test_update_image_metadata_with_bytes_body(self):
        self._test_image_metadata('update', True)

    def test_set_image_metadata_item_with_str_body(self):
        self._test_image_metadata()

    def test_set_image_metadata_item_with_bytes_body(self):
        self._test_image_metadata(bytes_body=True)

    def test_show_image_metadata_item_with_str_body(self):
        self._test_image_metadata('show_item')

    def test_show_image_metadata_item_with_bytes_body(self):
        self._test_image_metadata('show_item', True)

    def test_delete_image_metadata_item_with_str_body(self):
        self._test_image_metadata('delete_item')

    def test_delete_image_metadata_item_with_bytes_body(self):
        self._test_image_metadata('delete_item', True)

    def test_resource_delete_with_str_body(self):
        self._test_resource_deleted()

    def test_resource_delete_with_bytes_body(self):
        self._test_resource_deleted(True)
