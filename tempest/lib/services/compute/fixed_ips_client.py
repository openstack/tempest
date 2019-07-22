# Copyright 2013 IBM Corp
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

from tempest.lib.api_schema.response.compute.v2_1 import fixed_ips as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class FixedIPsClient(base_compute_client.BaseComputeClient):

    def show_fixed_ip(self, fixed_ip):
        url = "os-fixed-ips/%s" % fixed_ip
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_fixed_ip, resp, body)
        return rest_client.ResponseBody(resp, body)

    def reserve_fixed_ip(self, fixed_ip, **kwargs):
        """Reserve/Unreserve a fixed IP.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#reserve-or-release-a-fixed-ip
        """
        url = "os-fixed-ips/%s/action" % fixed_ip
        resp, body = self.post(url, json.dumps(kwargs))
        self.validate_response(schema.reserve_unreserve_fixed_ip, resp, body)
        return rest_client.ResponseBody(resp, body)
