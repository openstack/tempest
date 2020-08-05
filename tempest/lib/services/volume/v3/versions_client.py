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

from six.moves.urllib.parse import urljoin

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import versions as schema
from tempest.lib.common import rest_client
from tempest.lib.services.volume import base_client


class VersionsClient(base_client.BaseClient):

    def list_versions(self):
        """List API versions

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#list-all-api-versions
        """
        version_url = self._get_base_version_url()

        resp, body = self.raw_request(version_url, 'GET')
        # NOTE: We need a raw_request() here instead of request() call because
        # "list API versions" API doesn't require an authentication and we can
        # skip it with raw_request() call.
        self._error_checker(resp, body)

        body = json.loads(body)
        self.validate_response(schema.list_versions, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_version(self, version):
        """Show API version details

        Use raw_request in order to have access to the endpoints minus
        version and project in order to add version only back.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#show-api-v3-details
        """

        version_url = urljoin(self._get_base_version_url(), version + '/')
        headers = self.get_headers()
        headers['X-Auth-Token'] = self.token
        resp, body = self.raw_request(version_url, 'GET', headers=headers)
        self._error_checker(resp, body)
        body = json.loads(body)
        self.validate_response(schema.volume_api_version_details, resp, body)
        return rest_client.ResponseBody(resp, body)
