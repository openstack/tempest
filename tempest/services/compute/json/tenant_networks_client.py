# Copyright 2015 NEC Corporation. All rights reserved.
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

from tempest.api_schema.response.compute.v2_1 import tenant_networks as schema
from tempest.common import service_client


class TenantNetworksClientJSON(service_client.ServiceClient):

    def list_tenant_networks(self):
        resp, body = self.get("os-tenant-networks")
        body = json.loads(body)
        self.validate_response(schema.list_tenant_networks, resp, body)
        return service_client.ResponseBodyList(resp, body['networks'])

    def get_tenant_network(self, network_id):
        resp, body = self.get("os-tenant-networks/%s" % str(network_id))
        body = json.loads(body)
        self.validate_response(schema.get_tenant_network, resp, body)
        return service_client.ResponseBody(resp, body['network'])
