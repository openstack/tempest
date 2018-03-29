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

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.compute.v2_1 import limits as schemav21
from tempest.lib.api_schema.response.compute.v2_36 import limits as schemav236
from tempest.lib.api_schema.response.compute.v2_39 import limits as schemav239
from tempest.lib.api_schema.response.compute.v2_57 import limits as schemav257
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class LimitsClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.35', 'schema': schemav21},
        {'min': '2.36', 'max': '2.38', 'schema': schemav236},
        {'min': '2.39', 'max': '2.56', 'schema': schemav239},
        {'min': '2.57', 'max': None, 'schema': schemav257}]

    def show_limits(self):
        resp, body = self.get("limits")
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_limit, resp, body)
        return rest_client.ResponseBody(resp, body)
