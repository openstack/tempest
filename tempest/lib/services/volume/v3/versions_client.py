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

import time

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import versions as schema
from tempest.lib.common import rest_client
from tempest.lib.services.volume import base_client


class VersionsClient(base_client.BaseClient):

    def list_versions(self):
        """List API versions

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#list-all-api-versions
        """
        version_url = self._get_base_version_url()

        start = time.time()
        resp, body = self.raw_request(version_url, 'GET')
        end = time.time()
        # NOTE: We need a raw_request() here instead of request() call because
        # "list API versions" API doesn't require an authentication and we can
        # skip it with raw_request() call.
        self._log_request('GET', version_url, resp, secs=(end - start),
                          resp_body=body)
        self._error_checker(resp, body)

        body = json.loads(body)
        self.validate_response(schema.list_versions, resp, body)
        return rest_client.ResponseBody(resp, body)
