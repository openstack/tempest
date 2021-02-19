# Copyright 2012 OpenStack Foundation
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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.compute.v2_1 import floating_ips as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class FloatingIPPoolsClient(base_compute_client.BaseComputeClient):

    def list_floating_ip_pools(self, params=None):
        """Gets all floating IP Pools list."""
        url = 'os-floating-ip-pools'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_floating_ip_pools, resp, body)
        return rest_client.ResponseBody(resp, body)
