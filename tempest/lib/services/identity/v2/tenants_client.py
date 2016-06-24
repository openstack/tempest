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

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v2-ext.html#createTenant
        """
        post_body = json.dumps({'tenant': kwargs})
        resp, body = self.post('tenants', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_tenant(self, tenant_id):
        """Delete a tenant.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v2-ext.html#deleteTenant
        """
        resp, body = self.delete('tenants/%s' % str(tenant_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_tenant(self, tenant_id):
        """Get tenant details.

        Available params: see
            http://developer.openstack.org/
            api-ref-identity-v2-ext.html#admin-showTenantById
        """
        resp, body = self.get('tenants/%s' % str(tenant_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_tenants(self, **params):
        """Returns tenants.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v2-ext.html#admin-listTenants
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

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v2-ext.html#updateTenant
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

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v2-ext.html#listUsersForTenant
        """
        url = '/tenants/%s/users' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
