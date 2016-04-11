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

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.network import base


class PortsClient(base.BaseNetworkClient):

    def create_port(self, **kwargs):
        uri = '/ports'
        post_data = {'port': kwargs}
        return self.create_resource(uri, post_data)

    def update_port(self, port_id, **kwargs):
        uri = '/ports/%s' % port_id
        post_data = {'port': kwargs}
        return self.update_resource(uri, post_data)

    def show_port(self, port_id, **fields):
        uri = '/ports/%s' % port_id
        return self.show_resource(uri, **fields)

    def delete_port(self, port_id):
        uri = '/ports/%s' % port_id
        return self.delete_resource(uri)

    def list_ports(self, **filters):
        uri = '/ports'
        return self.list_resources(uri, **filters)

    def create_bulk_ports(self, **kwargs):
        """Create multiple ports in a single request.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2.html#bulkCreatePorts
        """
        uri = '/ports'
        return self.create_resource(uri, kwargs)

    def is_resource_deleted(self, id):
        try:
            self.show_port(id)
        except lib_exc.NotFound:
            return True
        return False
