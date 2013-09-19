# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import urllib

from tempest.common.rest_client import RestClient
from tempest import exceptions


class FloatingIPsClientJSON(RestClient):
    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FloatingIPsClientJSON, self).__init__(config, username, password,
                                                    auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_floating_ips(self, params=None):
        """Returns a list of all floating IPs filtered by any parameters."""
        url = 'os-floating-ips'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['floating_ips']

    def get_floating_ip_details(self, floating_ip_id):
        """Get the details of a floating IP."""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.get(url)
        body = json.loads(body)
        if resp.status == 404:
            raise exceptions.NotFound(body)
        return resp, body['floating_ip']

    def create_floating_ip(self, pool_name=None):
        """Allocate a floating IP to the project."""
        url = 'os-floating-ips'
        post_body = {'pool': pool_name}
        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body, self.headers)
        body = json.loads(body)
        return resp, body['floating_ip']

    def delete_floating_ip(self, floating_ip_id):
        """Deletes the provided floating IP from the project."""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.delete(url)
        return resp, body

    def associate_floating_ip_to_server(self, floating_ip, server_id):
        """Associate the provided floating IP to a specific server."""
        url = "servers/%s/action" % str(server_id)
        post_body = {
            'addFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body, self.headers)
        return resp, body

    def disassociate_floating_ip_from_server(self, floating_ip, server_id):
        """Disassociate the provided floating IP from a specific server."""
        url = "servers/%s/action" % str(server_id)
        post_body = {
            'removeFloatingIp': {
                'address': floating_ip,
            }
        }

        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body, self.headers)
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_floating_ip_details(id)
        except exceptions.NotFound:
            return True
        return False
