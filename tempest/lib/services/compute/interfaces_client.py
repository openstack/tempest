# Copyright 2013 IBM Corp.
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

from tempest.lib.api_schema.response.compute.v2_1 import interfaces as schema
from tempest.lib.api_schema.response.compute.v2_70 import interfaces as \
    schemav270
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class InterfacesClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.69', 'schema': schema},
        {'min': '2.70', 'max': None, 'schema': schemav270}]

    def list_interfaces(self, server_id):
        resp, body = self.get('servers/%s/os-interface' % server_id)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_interfaces, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_interface(self, server_id, **kwargs):
        """Create an interface.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-interface
        """
        post_body = {'interfaceAttachment': kwargs}
        post_body = json.dumps(post_body)
        resp, body = self.post('servers/%s/os-interface' % server_id,
                               body=post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_create_interfaces, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_interface(self, server_id, port_id):
        resp, body = self.get('servers/%s/os-interface/%s' % (server_id,
                                                              port_id))
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_create_interfaces, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_interface(self, server_id, port_id):
        resp, body = self.delete('servers/%s/os-interface/%s' % (server_id,
                                                                 port_id))
        self.validate_response(schema.delete_interface, resp, body)
        return rest_client.ResponseBody(resp, body)
