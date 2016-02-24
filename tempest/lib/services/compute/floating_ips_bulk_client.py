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

from tempest.lib.api_schema.response.compute.v2_1 import floating_ips as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class FloatingIPsBulkClient(base_compute_client.BaseComputeClient):

    def create_floating_ips_bulk(self, ip_range, pool, interface):
        """Allocate floating IPs in bulk."""
        post_body = {
            'ip_range': ip_range,
            'pool': pool,
            'interface': interface
        }
        post_body = json.dumps({'floating_ips_bulk_create': post_body})
        resp, body = self.post('os-floating-ips-bulk', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_floating_ips_bulk, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_floating_ips_bulk(self):
        """Gets all floating IPs in bulk."""
        resp, body = self.get('os-floating-ips-bulk')
        body = json.loads(body)
        self.validate_response(schema.list_floating_ips_bulk, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_floating_ips_bulk(self, ip_range):
        """Deletes the provided floating IPs in bulk."""
        post_body = json.dumps({'ip_range': ip_range})
        resp, body = self.put('os-floating-ips-bulk/delete', post_body)
        body = json.loads(body)
        self.validate_response(schema.delete_floating_ips_bulk, resp, body)
        return rest_client.ResponseBody(resp, body)
