# Copyright 2015 Red Hat, Inc.
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


class TenantsClient(rest_client.RestClient):
    api_version = "v2.0"

    def create_tenant(self, **kwargs):
        """Create a tenant

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#create-tenant
        """
        post_body = json.dumps({'tenant': kwargs})
        resp, body = self.post('tenants', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_tenant(self, tenant_id):
        """Delete a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#delete-tenant
        """
        resp, body = self.delete('tenants/%s' % str(tenant_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_tenant(self, tenant_id):
        """Get tenant details.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#show-tenant-details-by-id
        """
        resp, body = self.get('tenants/%s' % str(tenant_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_tenants(self, **params):
        """Returns tenants.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#list-tenants-admin-endpoint
        """
        url = 'tenants'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_tenant(self, tenant_id, **kwargs):
        """Updates a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#update-tenant
        """
        if 'id' not in kwargs:
            kwargs['id'] = tenant_id
        post_body = json.dumps({'tenant': kwargs})
        resp, body = self.post('tenants/%s' % tenant_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_tenant_users(self, tenant_id, **params):
        """List users for a Tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#list-users-on-a-tenant
        """
        url = '/tenants/%s/users' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
