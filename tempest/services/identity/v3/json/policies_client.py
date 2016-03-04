# Copyright 2013 OpenStack Foundation
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

"""
http://developer.openstack.org/api-ref-identity-v3.html#policies-v3
"""

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class PoliciesClient(rest_client.RestClient):
    api_version = "v3"

    def create_policy(self, **kwargs):
        """Creates a Policy.

        Available params: see http://developer.openstack.org/
                          api-ref-identity-v3.html#createPolicy
        """
        post_body = json.dumps({'policy': kwargs})
        resp, body = self.post('policies', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_policies(self):
        """Lists the policies."""
        resp, body = self.get('policies')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_policy(self, policy_id):
        """Lists out the given policy."""
        url = 'policies/%s' % policy_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_policy(self, policy_id, **kwargs):
        """Updates a policy.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#updatePolicy
        """
        post_body = json.dumps({'policy': kwargs})
        url = 'policies/%s' % policy_id
        resp, body = self.patch(url, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_policy(self, policy_id):
        """Deletes the policy."""
        url = "policies/%s" % policy_id
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
