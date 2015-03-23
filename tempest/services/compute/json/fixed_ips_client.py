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

import json

from tempest.api_schema.response.compute.v2_1 import fixed_ips as schema
from tempest.common import service_client


class FixedIPsClientJSON(service_client.ServiceClient):

    def get_fixed_ip_details(self, fixed_ip):
        url = "os-fixed-ips/%s" % (fixed_ip)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_fixed_ip, resp, body)
        return service_client.ResponseBody(resp, body['fixed_ip'])

    def reserve_fixed_ip(self, ip, body):
        """This reserves and unreserves fixed ips."""
        url = "os-fixed-ips/%s/action" % (ip)
        resp, body = self.post(url, json.dumps(body))
        self.validate_response(schema.reserve_fixed_ip, resp, body)
        return service_client.ResponseBody(resp)
