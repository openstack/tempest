# Copyright 2017 IBM Corp.
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

import fixtures

from tempest.lib.services import clients


class RegistryFixture(fixtures.Fixture):
    """A fixture to setup a test client registry

    The clients registry is a singleton. In Tempest it's filled with
    content from configuration. When testing Tempest lib classes without
    configuration it's handy to have the registry setup to be able to access
    service client factories.

    This fixture sets up the registry using a fake plugin, which includes all
    services specified at __init__ time. Any other plugin in the registry
    is removed at setUp time. The fake plugin is removed from the registry
    on cleanup.
    """

    PLUGIN_NAME = 'fake_plugin_for_test'

    def __init__(self):
        """Initialise the registry fixture"""
        self.services = set(['compute', 'identity.v2', 'identity.v3',
                             'image.v1', 'image.v2', 'network', 'placement',
                             'volume.v2', 'volume.v3', 'object-storage'])

    def _setUp(self):
        # Cleanup the registry
        registry = clients.ClientsRegistry()
        registry._service_clients = {}
        # Prepare the clients for registration
        all_clients = []
        service_clients = clients.tempest_modules()
        for sc in self.services:
            sc_module = service_clients[sc]
            sc_unversioned = sc.split('.')[0]
            sc_name = sc.replace('.', '_').replace('-', '_')
            # Pass the bare minimum params to satisfy the clients interface
            service_client_data = dict(
                name=sc_name, service_version=sc, service=sc_unversioned,
                module_path=sc_module.__name__,
                client_names=sc_module.__all__)
            all_clients.append(service_client_data)
        registry.register_service_client(self.PLUGIN_NAME, all_clients)

        def _cleanup():
            del registry._service_clients[self.PLUGIN_NAME]

        self.addCleanup(_cleanup)
