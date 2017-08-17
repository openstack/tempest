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

from tempest.lib.common import rest_client


class BulkMiddlewareClient(rest_client.RestClient):

    def upload_archive(self, upload_path, data,
                       archive_file_format='tar', headers=None):
        """Expand tar files into a Swift cluster.

        To extract containers and objects on Swift cluster from
        uploaded archived file. For More information please check:
        https://docs.openstack.org/swift/latest/middleware.html#module-swift.common.middleware.bulk
        """
        url = '%s?extract-archive=%s' % (upload_path, archive_file_format)
        if headers is None:
            headers = {}
        resp, body = self.put(url, data, headers)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def delete_bulk_data(self, data=None, headers=None):
        """Delete multiple objects or containers from their account.

        For More information please check:
        https://docs.openstack.org/swift/latest/middleware.html#module-swift.common.middleware.bulk
        """
        url = '?bulk-delete'

        if headers is None:
            headers = {}
        resp, body = self.delete(url, headers, data)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def delete_bulk_data_with_post(self, data=None, headers=None):
        """Delete multiple objects or containers with POST request.

        For More information please check:
        https://docs.openstack.org/swift/latest/middleware.html#module-swift.common.middleware.bulk
        """
        url = '?bulk-delete'

        if headers is None:
            headers = {}
        resp, body = self.post(url, data, headers)
        self.expected_success([200, 204], resp.status)
        return rest_client.ResponseBodyData(resp, body)
