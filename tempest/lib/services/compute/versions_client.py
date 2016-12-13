# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

from oslo_serialization import jsonutils as json
from six.moves import urllib

from tempest.lib.api_schema.response.compute.v2_1 import versions as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class VersionsClient(base_compute_client.BaseComputeClient):

    def _get_base_version_url(self):
        # NOTE: The URL which is got from keystone's catalog contains
        # API version and project-id like "/app-name/v2/{project-id}" or
        # "/v2/{project-id}", but we need to access the URL which doesn't
        # contain API version for getting API versions. For that, here
        # should use raw_request() instead of get().
        endpoint = self.base_url
        url = urllib.parse.urlsplit(endpoint)
        new_path = re.split(r'(^|/)+v\d+(\.\d+)?', url.path)[0]
        url = list(url)
        url[2] = new_path + '/'
        return urllib.parse.urlunsplit(url)

    def list_versions(self):
        version_url = self._get_base_version_url()
        resp, body = self.raw_request(version_url, 'GET')
        body = json.loads(body)
        self.validate_response(schema.list_versions, resp, body)
        return rest_client.ResponseBody(resp, body)

    def get_version_by_url(self, version_url):
        """Get the version document by url.

        This gets the version document for a url, useful in testing
        the contents of things like /v2/ or /v2.1/ in Nova. That
        controller needs authenticated access, so we have to get
        ourselves a token before making the request.

        """
        # we need a token for this request
        resp, body = self.raw_request(version_url, 'GET',
                                      {'X-Auth-Token': self.token})
        body = json.loads(body)
        self.validate_response(schema.get_one_version, resp, body)
        return rest_client.ResponseBody(resp, body)
