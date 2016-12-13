# Copyright 2013 NEC Corporation
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

from tempest.lib.api_schema.response.compute.v2_1 import tenant_usages
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class TenantUsagesClient(base_compute_client.BaseComputeClient):

    def list_tenant_usages(self, **params):
        url = 'os-simple-tenant-usage'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(tenant_usages.list_tenant_usage, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_tenant_usage(self, tenant_id, **params):
        url = 'os-simple-tenant-usage/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(tenant_usages.get_tenant_usage, resp, body)
        return rest_client.ResponseBody(resp, body)
