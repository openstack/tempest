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

import json

from tempest.api_schema.response.compute.v2_1 import limits as schema
from tempest.common import service_client


class LimitsClientJSON(service_client.ServiceClient):

    def get_absolute_limits(self):
        resp, body = self.get("limits")
        body = json.loads(body)
        self.validate_response(schema.get_limit, resp, body)
        return service_client.ResponseBody(resp, body['limits']['absolute'])

    def get_specific_absolute_limit(self, absolute_limit):
        resp, body = self.get("limits")
        body = json.loads(body)
        self.validate_response(schema.get_limit, resp, body)
        if absolute_limit not in body['limits']['absolute']:
            return None
        else:
            return body['limits']['absolute'][absolute_limit]
