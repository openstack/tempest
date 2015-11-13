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

from tempest.api_schema.response.compute.v2_1 import keypairs as schemav21
from tempest.api_schema.response.compute.v2_2 import keypairs as schemav22
from tempest.common import service_client
from tempest.services.compute.json import base


class KeyPairsClient(base.BaseComputeClient):

    schema_versions_info = [{'min': None, 'max': '2.1', 'schema': schemav21},
                            {'min': '2.2', 'max': None, 'schema': schemav22}]

    def list_keypairs(self):
        resp, body = self.get("os-keypairs")
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_keypairs, resp, body)
        return service_client.ResponseBody(resp, body)

    def show_keypair(self, keypair_name):
        resp, body = self.get("os-keypairs/%s" % keypair_name)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_keypair, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_keypair(self, **kwargs):
        post_body = json.dumps({'keypair': kwargs})
        resp, body = self.post("os-keypairs", body=post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.create_keypair, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_keypair(self, keypair_name):
        resp, body = self.delete("os-keypairs/%s" % keypair_name)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.delete_keypair, resp, body)
        return service_client.ResponseBody(resp, body)
