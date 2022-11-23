# Copyright 2022 NEC Corporation.  All rights reserved.
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


class ServerExternalEventsTest(base.BaseV2ComputeAdminTest):
    """Test server external events test"""

    @decorators.idempotent_id('6bbf4723-61d2-4372-af55-7ba27f1c9ba6')
    def test_create_server_external_events(self):
        """Test create a server and add some external events"""
        server_id = self.create_test_server(wait_until='ACTIVE')['id']
        events = [
            {
                "name": "network-changed",
                "server_uuid": server_id,
            }
        ]
        client = self.os_admin.server_external_events_client
        events_resp = client.create_server_external_events(
            events=events)['events'][0]
        self.assertEqual(server_id, events_resp['server_uuid'])
        self.assertEqual('network-changed', events_resp['name'])
        self.assertEqual(200, events_resp['code'])
