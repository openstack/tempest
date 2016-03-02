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


class IdentityClient(rest_client.RestClient):
    api_version = "v2.0"

    def show_api_description(self):
        """Retrieves info about the v2.0 Identity API"""
        url = ''
        resp, body = self.get(url)
        self.expected_success([200, 203], resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_token(self, token_id):
        """Get token details."""
        resp, body = self.get("tokens/%s" % token_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_token(self, token_id):
        """Delete a token."""
        resp, body = self.delete("tokens/%s" % token_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_extensions(self):
        """List all the extensions."""
        resp, body = self.get('/extensions')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
