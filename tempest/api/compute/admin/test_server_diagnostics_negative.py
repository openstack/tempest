# Copyright 2017 Mirantis Inc.
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

from tempest.api.compute import base
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ServerDiagnosticsNegativeTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(ServerDiagnosticsNegativeTest, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e84e2234-60d2-42fa-8b30-e2d3049724ac')
    def test_get_server_diagnostics_by_non_admin(self):
        # Non-admin user cannot view server diagnostics according to policy
        server_id = self.create_test_server(wait_until='ACTIVE')['id']
        self.assertRaises(lib_exc.Forbidden,
                          self.client.show_server_diagnostics, server_id)
