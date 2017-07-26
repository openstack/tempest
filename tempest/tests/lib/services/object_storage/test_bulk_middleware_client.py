# Copyright 2017 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.object_storage import bulk_middleware_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestBulkMiddlewareClient(base.BaseServiceTest):

    def setUp(self):
        super(TestBulkMiddlewareClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = bulk_middleware_client.BulkMiddlewareClient(
            fake_auth, 'object-storage', 'regionOne')

    def test_upload_archive(self):
        url = 'test_path?extract-archive=tar'
        data = 'test_data'
        self.check_service_client_function(
            self.client.upload_archive,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            mock_args=[url, data, {}],
            resp_as_string=True,
            upload_path='test_path', data=data, archive_file_format='tar')

    def test_delete_bulk_data(self):
        url = '?bulk-delete'
        data = 'test_data'
        self.check_service_client_function(
            self.client.delete_bulk_data,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            mock_args=[url, {}, data],
            resp_as_string=True,
            data=data)

    def _test_delete_bulk_data_with_post(self, status):
        url = '?bulk-delete'
        data = 'test_data'
        self.check_service_client_function(
            self.client.delete_bulk_data_with_post,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            mock_args=[url, data, {}],
            resp_as_string=True,
            status=status,
            data=data)

    def test_delete_bulk_data_with_post_200(self):
        self._test_delete_bulk_data_with_post(200)

    def test_delete_bulk_data_with_post_204(self):
        self._test_delete_bulk_data_with_post(204)
