# Copyright (c) 2019 Ericsson
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

from tempest.lib.common import api_version_utils
from tempest.lib.common import rest_client

PLACEMENT_MICROVERSION = None


class BasePlacementClient(rest_client.RestClient):

    api_microversion_header_name = 'OpenStack-API-Version'
    version_header_value = 'placement %s'

    def get_headers(self):
        headers = super(BasePlacementClient, self).get_headers()
        if PLACEMENT_MICROVERSION:
            headers[self.api_microversion_header_name] = \
                self.version_header_value % PLACEMENT_MICROVERSION
        return headers

    def request(self, method, url, extra_headers=False, headers=None,
                body=None, chunked=False):
        resp, resp_body = super(BasePlacementClient, self).request(
            method, url, extra_headers, headers, body, chunked)
        if (PLACEMENT_MICROVERSION and
            PLACEMENT_MICROVERSION != api_version_utils.LATEST_MICROVERSION):
            api_version_utils.assert_version_header_matches_request(
                self.api_microversion_header_name,
                self.version_header_value % PLACEMENT_MICROVERSION,
                resp)
        return resp, resp_body
