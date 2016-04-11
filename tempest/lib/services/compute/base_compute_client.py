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

from tempest.lib.common import api_version_request
from tempest.lib.common import api_version_utils
from tempest.lib.common import rest_client
from tempest.lib import exceptions

COMPUTE_MICROVERSION = None


class BaseComputeClient(rest_client.RestClient):
    """Base compute service clients class to support microversion.

    This class adds microversion to API request header if that is set
    and provides interface to select appropriate JSON schema file for
    response validation.

    :param auth_provider: An auth provider object used to wrap requests in
                          auth
    :param str service: The service name to use for the catalog lookup
    :param str region: The region to use for the catalog lookup
    :param kwargs: kwargs required by rest_client.RestClient
    """

    api_microversion_header_name = 'X-OpenStack-Nova-API-Version'

    def __init__(self, auth_provider, service, region,
                 **kwargs):
        super(BaseComputeClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def get_headers(self):
        headers = super(BaseComputeClient, self).get_headers()
        if COMPUTE_MICROVERSION:
            headers[self.api_microversion_header_name] = COMPUTE_MICROVERSION
        return headers

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        resp, resp_body = super(BaseComputeClient, self).request(
            method, url, extra_headers, headers, body)
        if (COMPUTE_MICROVERSION and
            COMPUTE_MICROVERSION != api_version_utils.LATEST_MICROVERSION):
            api_version_utils.assert_version_header_matches_request(
                self.api_microversion_header_name,
                COMPUTE_MICROVERSION,
                resp)
        return resp, resp_body

    def get_schema(self, schema_versions_info):
        """Get JSON schema

        This method provides the matching schema for requested
        microversion.

        :param schema_versions_info: List of dict which provides schema
                                     information with range of valid versions.
        Example -
        schema_versions_info = [
            {'min': None, 'max': '2.1', 'schema': schemav21},
            {'min': '2.2', 'max': '2.9', 'schema': schemav22},
            {'min': '2.10', 'max': None, 'schema': schemav210}]
        """
        schema = None
        version = api_version_request.APIVersionRequest(COMPUTE_MICROVERSION)
        for items in schema_versions_info:
            min_version = api_version_request.APIVersionRequest(items['min'])
            max_version = api_version_request.APIVersionRequest(items['max'])
            # This is case where COMPUTE_MICROVERSION is None, which means
            # request without microversion So select base v2.1 schema.
            if version.is_null() and items['min'] is None:
                schema = items['schema']
                break
            # else select appropriate schema as per COMPUTE_MICROVERSION
            elif version.matches(min_version, max_version):
                schema = items['schema']
                break
        if schema is None:
            raise exceptions.JSONSchemaNotFound(
                version=version.get_string(),
                schema_versions_info=schema_versions_info)
        return schema
