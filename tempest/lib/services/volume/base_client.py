# Copyright 2016 Andrew Kerr
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

from tempest.lib.common import api_version_utils
from tempest.lib.common import rest_client

VOLUME_MICROVERSION = None


class BaseClient(rest_client.RestClient):
    """Base volume service clients class to support microversion."""
    api_microversion_header_name = 'Openstack-Api-Version'

    def get_headers(self, accept_type=None, send_type=None):
        headers = super(BaseClient, self).get_headers(
            accept_type=accept_type, send_type=send_type)
        if VOLUME_MICROVERSION:
            headers[self.api_microversion_header_name] = ('volume %s' %
                                                          VOLUME_MICROVERSION)
        return headers

    def request(self, method, url, extra_headers=False, headers=None,
                body=None, chunked=False):

        resp, resp_body = super(BaseClient, self).request(
            method, url, extra_headers, headers, body, chunked)
        if (VOLUME_MICROVERSION and
            VOLUME_MICROVERSION != api_version_utils.LATEST_MICROVERSION):
            api_version_utils.assert_version_header_matches_request(
                self.api_microversion_header_name,
                'volume %s' % VOLUME_MICROVERSION,
                resp)
        return resp, resp_body
