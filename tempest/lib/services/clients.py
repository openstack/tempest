# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

from tempest.lib.common.utils import misc
from tempest.lib import exceptions


@misc.singleton
class ClientsRegistry(object):
    """Registry of all service clients available from plugins"""

    def __init__(self):
        self._service_clients = {}

    def register_service_client(self, plugin_name, service_client_data):
        if plugin_name in self._service_clients:
            detailed_error = 'Clients for plugin %s already registered'
            raise exceptions.PluginRegistrationException(
                name=plugin_name,
                detailed_error=detailed_error % plugin_name)
        self._service_clients[plugin_name] = service_client_data

    def get_service_clients(self):
        return self._service_clients
