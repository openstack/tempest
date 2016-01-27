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

from tempest.common import api_version_request
from tempest.common import api_version_utils
from tempest import exceptions
from tempest.services import base_microversion_client


class BaseComputeClient(base_microversion_client.BaseMicroversionClient):

    def __init__(self, auth_provider, service, region,
                 api_microversion_header_name='X-OpenStack-Nova-API-Version',
                 **kwargs):
        super(BaseComputeClient, self).__init__(
            auth_provider, service, region,
            api_microversion_header_name, **kwargs)

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        resp, resp_body = super(BaseComputeClient, self).request(
            method, url, extra_headers, headers, body)
        if self.api_microversion and self.api_microversion != 'latest':
            api_version_utils.assert_version_header_matches_request(
                self.api_microversion_header_name,
                self.api_microversion,
                resp)
        return resp, resp_body

    def get_schema(self, schema_versions_info):
        """Get JSON schema

        This method provides the matching schema for requested
        microversion (self.api_microversion).
        :param schema_versions_info: List of dict which provides schema
        information with range of valid versions.
        Example -
        schema_versions_info = [
            {'min': None, 'max': '2.1', 'schema': schemav21},
            {'min': '2.2', 'max': '2.9', 'schema': schemav22},
            {'min': '2.10', 'max': None, 'schema': schemav210}]
        """
        schema = None
        version = api_version_request.APIVersionRequest(self.api_microversion)
        for items in schema_versions_info:
            min_version = api_version_request.APIVersionRequest(items['min'])
            max_version = api_version_request.APIVersionRequest(items['max'])
            # This is case where self.api_microversion is None, which means
            # request without microversion So select base v2.1 schema.
            if version.is_null() and items['min'] is None:
                schema = items['schema']
                break
            # else select appropriate schema as per self.api_microversion
            elif version.matches(min_version, max_version):
                schema = items['schema']
                break
        if schema is None:
            raise exceptions.JSONSchemaNotFound(
                version=version.get_string(),
                schema_versions_info=schema_versions_info)
        return schema
