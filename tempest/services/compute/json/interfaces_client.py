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

from tempest.common.rest_client import RestClient
from tempest import config
from tempest import exceptions

CONF = config.CONF


class InterfacesClientJSON(RestClient):

    def __init__(self, auth_provider):
        super(InterfacesClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def list_interfaces(self, server):
        resp, body = self.get('servers/%s/os-interface' % server)
        body = json.loads(body)
        return resp, body['interfaceAttachments']

    def create_interface(self, server, port_id=None, network_id=None,
                         fixed_ip=None):
        post_body = dict(interfaceAttachment=dict())
        if port_id:
            post_body['interfaceAttachment']['port_id'] = port_id
        if network_id:
            post_body['interfaceAttachment']['net_id'] = network_id
        if fixed_ip:
            fip = dict(ip_address=fixed_ip)
            post_body['interfaceAttachment']['fixed_ips'] = [fip]
        post_body = json.dumps(post_body)
        resp, body = self.post('servers/%s/os-interface' % server,
                               headers=self.headers,
                               body=post_body)
        body = json.loads(body)
        return resp, body['interfaceAttachment']

    def show_interface(self, server, port_id):
        resp, body = self.get('servers/%s/os-interface/%s' % (server, port_id))
        body = json.loads(body)
        return resp, body['interfaceAttachment']

    def delete_interface(self, server, port_id):
        resp, body = self.delete('servers/%s/os-interface/%s' % (server,
                                                                 port_id))
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
