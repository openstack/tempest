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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class VersionsClient(rest_client.RestClient):
    api_version = "v3"

    def list_versions(self):
        """List API versions"""
        version_url = self._get_base_version_url()

        resp, body = self.raw_request(version_url, 'GET')
        self._error_checker(resp, body)

        self.expected_success(300, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
