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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class DomainsClient(rest_client.RestClient):
    api_version = "v3"

    def create_domain(self, **kwargs):
        """Creates a domain.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-domain
        """
        post_body = json.dumps({'domain': kwargs})
        resp, body = self.post('domains', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_domain(self, domain_id):
        """Deletes a domain.

        For APi details, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-domain
        """
        resp, body = self.delete('domains/%s' % domain_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_domains(self, **params):
        """List Domains.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#list-domains
        """
        url = 'domains'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_domain(self, domain_id, **kwargs):
        """Updates a domain.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-domain
        """
        post_body = json.dumps({'domain': kwargs})
        resp, body = self.patch('domains/%s' % domain_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_domain(self, domain_id):
        """Get Domain details.

        For API details, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-domain-details
        """
        resp, body = self.get('domains/%s' % domain_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
