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

from oslo_serialization import jsonutils as json
from six.moves import urllib

from tempest.api_schema.response.compute.v2_1 import versions as schema
from tempest.common import service_client


class VersionsClient(service_client.ServiceClient):

    def list_versions(self):
        # NOTE: The URL which is gotten from keystone's catalog contains
        # API version and project-id like "v2/{project-id}", but we need
        # to access the URL which doesn't contain them for getting API
        # versions. For that, here should use raw_request() instead of
        # get().
        endpoint = self.base_url
        url = urllib.parse.urlparse(endpoint)
        version_url = '%s://%s/' % (url.scheme, url.netloc)

        resp, body = self.raw_request(version_url, 'GET')
        body = json.loads(body)
        self.validate_response(schema.list_versions, resp, body)
        return service_client.ResponseBody(resp, body)
