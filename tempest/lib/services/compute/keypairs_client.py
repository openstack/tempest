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
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import keypairs as schemav21
from tempest.lib.api_schema.response.compute.v2_2 import keypairs as schemav22
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class KeyPairsClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [{'min': None, 'max': '2.1', 'schema': schemav21},
                            {'min': '2.2', 'max': None, 'schema': schemav22}]

    def list_keypairs(self, **params):
        """Lists keypairs that are associated with the account.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-keypairs
        """
        url = 'os-keypairs'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_keypairs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_keypair(self, keypair_name, **params):
        """Shows details for a keypair that is associated with the account.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#show-keypair-details
        """
        url = "os-keypairs/%s" % keypair_name
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_keypair, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_keypair(self, **kwargs):
        """Create a keypair.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-or-import-keypair
        """
        post_body = json.dumps({'keypair': kwargs})
        resp, body = self.post("os-keypairs", body=post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.create_keypair, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_keypair(self, keypair_name, **params):
        """Deletes a keypair.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-keypair
        """
        url = "os-keypairs/%s" % keypair_name
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.delete(url)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.delete_keypair, resp, body)
        return rest_client.ResponseBody(resp, body)
