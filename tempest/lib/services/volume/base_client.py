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

from tempest.lib.common import api_version_request
from tempest.lib.common import api_version_utils
from tempest.lib.common import rest_client
from tempest.lib import exceptions

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

    def get_schema(self, schema_versions_info):
        """Get JSON schema

        This method provides the matching schema for requested
        microversion.

        :param schema_versions_info: List of dict which provides schema
                                     information with range of valid versions.

        Example::

         schema_versions_info = [
             {'min': None, 'max': '2.1', 'schema': schemav21},
             {'min': '2.2', 'max': '2.9', 'schema': schemav22},
             {'min': '2.10', 'max': None, 'schema': schemav210}]
        """
        schema = None
        version = api_version_request.APIVersionRequest(VOLUME_MICROVERSION)
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
