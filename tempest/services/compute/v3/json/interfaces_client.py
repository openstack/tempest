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

import json
import time

from tempest.api_schema.response.compute import interfaces as common_schema
from tempest.api_schema.response.compute import servers as servers_schema
from tempest.api_schema.response.compute.v3 import interfaces as schema
from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class InterfacesV3ClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(InterfacesV3ClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_v3_type

    def list_interfaces(self, server):
        resp, body = self.get('servers/%s/os-attach-interfaces' % server)
        body = json.loads(body)
        self.validate_response(schema.list_interfaces, resp, body)
        return resp, body['interface_attachments']

    def create_interface(self, server, port_id=None, network_id=None,
                         fixed_ip=None):
        post_body = dict()
        if port_id:
            post_body['port_id'] = port_id
        if network_id:
            post_body['net_id'] = network_id
        if fixed_ip:
            post_body['fixed_ips'] = [dict(ip_address=fixed_ip)]
        post_body = json.dumps({'interface_attachment': post_body})
        resp, body = self.post('servers/%s/os-attach-interfaces' % server,
                               body=post_body)
        body = json.loads(body)
        return resp, body['interface_attachment']

    def show_interface(self, server, port_id):
        resp, body =\
            self.get('servers/%s/os-attach-interfaces/%s' % (server, port_id))
        body = json.loads(body)
        return resp, body['interface_attachment']

    def delete_interface(self, server, port_id):
        resp, body =\
            self.delete('servers/%s/os-attach-interfaces/%s' % (server,
                                                                port_id))
        self.validate_response(common_schema.delete_interface, resp, body)
        return resp, body

    def wait_for_interface_status(self, server, port_id, status):
        """Waits for a interface to reach a given status."""
        resp, body = self.show_interface(server, port_id)
        interface_status = body['port_state']
        start = int(time.time())

        while(interface_status != status):
            time.sleep(self.build_interval)
            resp, body = self.show_interface(server, port_id)
            interface_status = body['port_state']

            timed_out = int(time.time()) - start >= self.build_timeout

            if interface_status != status and timed_out:
                message = ('Interface %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (port_id, status, self.build_timeout))
                raise exceptions.TimeoutException(message)

        return resp, body

    def add_fixed_ip(self, server_id, network_id):
        """Add a fixed IP to input server instance."""
        post_body = json.dumps({
            'add_fixed_ip': {
                'network_id': network_id
            }
        })
        resp, body = self.post('servers/%s/action' % str(server_id),
                               post_body)
        self.validate_response(servers_schema.server_actions_common_schema,
                               resp, body)
        return resp, body

    def remove_fixed_ip(self, server_id, ip_address):
        """Remove input fixed IP from input server instance."""
        post_body = json.dumps({
            'remove_fixed_ip': {
                'address': ip_address
            }
        })
        resp, body = self.post('servers/%s/action' % str(server_id),
                               post_body)
        self.validate_response(servers_schema.server_actions_common_schema,
                               resp, body)
        return resp, body
