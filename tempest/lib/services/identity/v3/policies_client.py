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
https://docs.openstack.org/api-ref/identity/v3/index.html#policies
"""

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class PoliciesClient(rest_client.RestClient):
    api_version = "v3"

    def create_policy(self, **kwargs):
        """Creates a Policy.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-policy
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

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-policy
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

    def update_policy_association_for_endpoint(self, policy_id, endpoint_id):
        """Create policy association with endpoint.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#associate-policy-and-endpoint
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/endpoints/{1}"\
              .format(policy_id, endpoint_id)
        resp, body = self.put(url, '{}')
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_policy_association_for_endpoint(self, policy_id, endpoint_id):
        """Get policy association of endpoint.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#verify-a-policy-and-endpoint-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/endpoints/{1}"\
              .format(policy_id, endpoint_id)
        resp, body = self.get(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_policy_association_for_endpoint(self, policy_id, endpoint_id):
        """Delete policy association with endpoint.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-a-policy-and-endpoint-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/endpoints/{1}"\
              .format(policy_id, endpoint_id)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_policy_association_for_service(self, policy_id, service_id):
        """Create policy association with service.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#associate-policy-and-service-type-endpoint
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}"\
              .format(policy_id, service_id)
        resp, body = self.put(url, '{}')
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_policy_association_for_service(self, policy_id, service_id):
        """Get policy association of service.

        API Reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#verify-a-policy-and-service-type-endpoint-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}"\
              .format(policy_id, service_id)
        resp, body = self.get(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_policy_association_for_service(self, policy_id, service_id):
        """Delete policy association with service.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-a-policy-and-service-type-endpoint-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}"\
              .format(policy_id, service_id)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_policy_association_for_region_and_service(
            self, policy_id, service_id, region_id):
        """Create policy association with service and region.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#associate-policy-and-service-type-endpoint-in-a-region
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}/regions/{2}"\
              .format(policy_id, service_id, region_id)
        resp, body = self.put(url, '{}')
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_policy_association_for_region_and_service(
        self, policy_id, service_id, region_id):
        """Get policy association of service and region.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#verify-a-policy-and-service-type-endpoint-in-a-region-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}/regions/{2}"\
              .format(policy_id, service_id, region_id)
        resp, body = self.get(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_policy_association_for_region_and_service(
        self, policy_id, service_id, region_id):
        """Delete policy association with service and region.

        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-a-policy-and-service-type-endpoint-in-a-region-association
        """
        url = "policies/{0}/OS-ENDPOINT-POLICY/services/{1}/regions/{2}"\
              .format(policy_id, service_id, region_id)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
