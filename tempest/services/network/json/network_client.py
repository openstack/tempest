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

import time

from tempest import exceptions
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.network import base


class NetworkClient(base.BaseNetworkClient):

    """Tempest REST client for Neutron.

    Uses v2 of the Neutron API, since the V1 API has been removed from the
    code base.

    Implements create, delete, update, list and show for the basic Neutron
    abstractions (networks, sub-networks, routers, ports and floating IP):

    Implements add/remove interface to router using subnet ID / port ID

    It also implements list, show, update and reset for OpenStack Networking
    quotas
    """

    def wait_for_resource_deletion(self, resource_type, id, client=None):
        """Waits for a resource to be deleted."""
        start_time = int(time.time())
        while True:
            if self.is_resource_deleted(resource_type, id, client=client):
                return
            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException
            time.sleep(self.build_interval)

    def is_resource_deleted(self, resource_type, id, client=None):
        if client is None:
            client = self
        method = 'show_' + resource_type
        try:
            getattr(client, method)(id)
        except AttributeError:
            raise Exception("Unknown resource type %s " % resource_type)
        except lib_exc.NotFound:
            return True
        return False
