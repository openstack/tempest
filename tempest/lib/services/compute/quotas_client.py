# Copyright 2012 NTT Data
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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import quotas as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class QuotasClient(base_compute_client.BaseComputeClient):

    def show_quota_set(self, tenant_id, user_id=None, detail=False):
        """List the quota set for a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#show-a-quota
        https://developer.openstack.org/api-ref/compute/#show-the-detail-of-quota
        """

        params = {}
        url = 'os-quota-sets/%s' % tenant_id
        if detail:
            url += '/detail'
        if user_id:
            params.update({'user_id': user_id})
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        if detail:
            self.validate_response(schema.get_quota_set_details, resp, body)
        else:
            self.validate_response(schema.get_quota_set, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_default_quota_set(self, tenant_id):
        """List the default quota set for a tenant.

        https://developer.openstack.org/api-ref/compute/#list-default-quotas-for-tenant
        """

        url = 'os-quota-sets/%s/defaults' % tenant_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_quota_set, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_quota_set(self, tenant_id, user_id=None, **kwargs):
        """Updates the tenant's quota limits for one or more resources.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#update-quotas
        """

        post_body = json.dumps({'quota_set': kwargs})

        if user_id:
            resp, body = self.put('os-quota-sets/%s?user_id=%s' %
                                  (tenant_id, user_id), post_body)
        else:
            resp, body = self.put('os-quota-sets/%s' % tenant_id,
                                  post_body)

        body = json.loads(body)
        self.validate_response(schema.update_quota_set, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_quota_set(self, tenant_id):
        """Delete the tenant's quota set.

        https://developer.openstack.org/api-ref/compute/#revert-quotas-to-defaults
        """
        resp, body = self.delete('os-quota-sets/%s' % tenant_id)
        self.validate_response(schema.delete_quota, resp, body)
        return rest_client.ResponseBody(resp, body)
