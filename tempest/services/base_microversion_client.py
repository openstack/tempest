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

from tempest_lib.common import rest_client


class BaseMicroversionClient(rest_client.RestClient):
    """Base class to support microversion in service clients

    This class is used to support microversion in service clients.
    This provides feature to make API request with microversion.
    Service clients derived from this class will be able to send API
    request to server with or without microversion.
    If api_microversion is not set on service client then API request will be
    normal request without microversion.

    """
    def __init__(self, auth_provider, service, region,
                 api_microversion_header_name, **kwargs):
        """Base Microversion Client __init__

        :param auth_provider: an auth provider object used to wrap requests in
                              auth
        :param str service: The service name to use for the catalog lookup
        :param str region: The region to use for the catalog lookup
        :param str api_microversion_header_name: The microversion header name
                                                 to use for sending API
                                                 request with microversion
        :param kwargs: kwargs required by rest_client.RestClient
        """
        super(BaseMicroversionClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.api_microversion_header_name = api_microversion_header_name
        self.api_microversion = None

    def get_headers(self):
        headers = super(BaseMicroversionClient, self).get_headers()
        if self.api_microversion:
            headers[self.api_microversion_header_name] = self.api_microversion
        return headers

    def set_api_microversion(self, microversion):
        self.api_microversion = microversion
