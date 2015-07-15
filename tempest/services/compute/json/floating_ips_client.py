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
from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import floating_ips as schema
from tempest.common import service_client


class FloatingIPsClient(service_client.ServiceClient):

    def list_floating_ips(self, params=None):
        """Returns a list of all floating IPs filtered by any parameters."""
        url = 'os-floating-ips'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_floating_ips, resp, body)
        return service_client.ResponseBodyList(resp, body['floating_ips'])

    def show_floating_ip(self, floating_ip_id):
        """Get the details of a floating IP."""
        url = "os-floating-ips/%s" % floating_ip_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.create_get_floating_ip, resp, body)
        return service_client.ResponseBody(resp, body['floating_ip'])

    def create_floating_ip(self, pool_name=None):
        """Allocate a floating IP to the project."""
        url = 'os-floating-ips'
        post_body = {'pool': pool_name}
        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_get_floating_ip, resp, body)
        return service_client.ResponseBody(resp, body['floating_ip'])

    def delete_floating_ip(self, floating_ip_id):
        """Deletes the provided floating IP from the project."""
        url = "os-floating-ips/%s" % floating_ip_id
        resp, body = self.delete(url)
        self.validate_response(schema.add_remove_floating_ip, resp, body)
        return service_client.ResponseBody(resp, body)

    def associate_floating_ip_to_server(self, floating_ip, server_id):
        """Associate the provided floating IP to a specific server."""
        url = "servers/%s/action" % server_id
        post_body = {
            'addFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body)
        self.validate_response(schema.add_remove_floating_ip, resp, body)
        return service_client.ResponseBody(resp, body)

    def disassociate_floating_ip_from_server(self, floating_ip, server_id):
        """Disassociate the provided floating IP from a specific server."""
        url = "servers/%s/action" % server_id
        post_body = {
            'removeFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body)
        self.validate_response(schema.add_remove_floating_ip, resp, body)
        return service_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_floating_ip(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'floating_ip'
