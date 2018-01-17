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

from tempest.api.compute import base
from tempest.common import waiters
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ListServersNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ListServersNegativeTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ListServersNegativeTestJSON, cls).resource_setup()

        # The following servers are created for use
        # by the test methods in this class. These
        # servers are cleaned up automatically in the
        # tearDownClass method of the super-class.
        body = cls.create_test_server(wait_until='ACTIVE', min_count=3)

        # delete one of the created servers
        cls.deleted_id = body['server']['id']
        cls.client.delete_server(cls.deleted_id)
        waiters.wait_for_server_termination(cls.client, cls.deleted_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('24a26f1a-1ddc-4eea-b0d7-a90cc874ad8f')
    def test_list_servers_with_a_deleted_server(self):
        # Verify deleted servers do not show by default in list servers
        # List servers and verify server not returned
        body = self.client.list_servers()
        servers = body['servers']
        actual = [srv for srv in servers
                  if srv['id'] == self.deleted_id]
        self.assertEmpty(actual)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ff01387d-c7ad-47b4-ae9e-64fa214638fe')
    def test_list_servers_by_non_existing_image(self):
        # Listing servers for a non existing image returns empty list
        body = self.client.list_servers(image='non_existing_image')
        servers = body['servers']
        self.assertEmpty(servers)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5913660b-223b-44d4-a651-a0fbfd44ca75')
    def test_list_servers_by_non_existing_flavor(self):
        # Listing servers by non existing flavor returns empty list
        body = self.client.list_servers(flavor='non_existing_flavor')
        servers = body['servers']
        self.assertEmpty(servers)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e2c77c4a-000a-4af3-a0bd-629a328bde7c')
    def test_list_servers_by_non_existing_server_name(self):
        # Listing servers for a non existent server name returns empty list
        body = self.client.list_servers(name='non_existing_server_name')
        servers = body['servers']
        self.assertEmpty(servers)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fcdf192d-0f74-4d89-911f-1ec002b822c4')
    def test_list_servers_status_non_existing(self):
        # Return an empty list when invalid status is specified
        body = self.client.list_servers(status='non_existing_status')
        servers = body['servers']
        self.assertEmpty(servers)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d47c17fb-eebd-4287-8e95-f20a7e627b18')
    def test_list_servers_by_limits_greater_than_actual_count(self):
        # Gather the complete list of servers in the project for reference
        full_list = self.client.list_servers()['servers']
        # List servers by specifying a greater value for limit
        limit = len(full_list) + 100
        body = self.client.list_servers(limit=limit)
        self.assertEqual(len(full_list), len(body['servers']))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('679bc053-5e70-4514-9800-3dfab1a380a6')
    def test_list_servers_by_limits_pass_string(self):
        # Return an error if a string value is passed for limit
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          limit='testing')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('62610dd9-4713-4ee0-8beb-fd2c1aa7f950')
    def test_list_servers_by_limits_pass_negative_value(self):
        # Return an error if a negative value for limit is passed
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          limit=-1)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('87d12517-e20a-4c9c-97b6-dd1628d6d6c9')
    def test_list_servers_by_changes_since_invalid_date(self):
        # Return an error when invalid date format is passed
        params = {'changes-since': '2011/01/01'}
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          **params)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('74745ad8-b346-45b5-b9b8-509d7447fc1f')
    def test_list_servers_by_changes_since_future_date(self):
        # Return an empty list when a date in the future is passed.
        # updated_at field may haven't been set at the point in the boot
        # process where build_request still exists, so add
        # {'status': 'ACTIVE'} along with changes-since as filter.
        changes_since = {'changes-since': '2051-01-01T12:34:00Z',
                         'status': 'ACTIVE'}
        body = self.client.list_servers(**changes_since)
        self.assertEmpty(body['servers'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('93055106-2d34-46fe-af68-d9ddbf7ee570')
    def test_list_servers_detail_server_is_deleted(self):
        # Server details are not listed for a deleted server
        body = self.client.list_servers(detail=True)
        servers = body['servers']
        actual = [srv for srv in servers
                  if srv['id'] == self.deleted_id]
        self.assertEmpty(actual)
