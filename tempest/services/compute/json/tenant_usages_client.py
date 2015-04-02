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

import json
import urllib

from tempest.api_schema.response.compute.v2_1 import tenant_usages as schema
from tempest.common import service_client


class TenantUsagesClientJSON(service_client.ServiceClient):

    def list_tenant_usages(self, params=None):
        url = 'os-simple-tenant-usage'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_tenant, resp, body)
        return service_client.ResponseBodyList(resp, body['tenant_usages'][0])

    def get_tenant_usage(self, tenant_id, params=None):
        url = 'os-simple-tenant-usage/%s' % tenant_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_tenant, resp, body)
        return service_client.ResponseBodyList(resp, body['tenant_usage'])
