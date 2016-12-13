# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

from oslo_serialization import jsonutils
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class BaseQuotasClient(rest_client.RestClient):
    """Client class to send CRUD Volume Quotas API requests"""

    def show_default_quota_set(self, tenant_id):
        """List the default volume quota set for a tenant."""

        url = 'os-quota-sets/%s/defaults' % tenant_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = jsonutils.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_quota_set(self, tenant_id, params=None):
        """List the quota set for a tenant."""

        url = 'os-quota-sets/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = jsonutils.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_quota_set(self, tenant_id, **kwargs):
        """Updates quota set

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#updateQuotas-v2
        """
        put_body = jsonutils.dumps({'quota_set': kwargs})
        resp, body = self.put('os-quota-sets/%s' % tenant_id, put_body)
        self.expected_success(200, resp.status)
        body = jsonutils.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_quota_set(self, tenant_id):
        """Delete the tenant's quota set."""
        resp, body = self.delete('os-quota-sets/%s' % tenant_id)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
