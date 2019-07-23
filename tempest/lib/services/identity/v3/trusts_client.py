# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class TrustsClient(rest_client.RestClient):
    api_version = "v3"

    def create_trust(self, **kwargs):
        """Creates a trust.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#create-trust
        """
        post_body = json.dumps({'trust': kwargs})
        resp, body = self.post('OS-TRUST/trusts', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_trust(self, trust_id):
        """Deletes a trust."""
        resp, body = self.delete("OS-TRUST/trusts/%s" % trust_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_trusts(self, **params):
        """Returns trusts

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#list-trusts
        """
        url = "OS-TRUST/trusts/"
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_trust(self, trust_id):
        """GET trust."""
        resp, body = self.get("OS-TRUST/trusts/%s" % trust_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_trust_roles(self, trust_id):
        """GET roles delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles" % trust_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_trust_role(self, trust_id, role_id):
        """GET role delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles/%s"
                              % (trust_id, role_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_trust_role(self, trust_id, role_id):
        """HEAD Check if role is delegated by a trust."""
        resp, body = self.head("OS-TRUST/trusts/%s/roles/%s"
                               % (trust_id, role_id))
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
