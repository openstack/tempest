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

from six import moves
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ListServersNegativeTestJSON(base.BaseV2ComputeTest):
    force_tenant_isolation = True

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
        cls.existing_fixtures = []
        cls.deleted_fixtures = []
        for x in moves.xrange(2):
            srv = cls.create_test_server(wait_until='ACTIVE')
            cls.existing_fixtures.append(srv)

        srv = cls.create_test_server()
        cls.client.delete_server(srv['id'])
        # We ignore errors on termination because the server may
        # be put into ERROR status on a quick spawn, then delete,
        # as the compute node expects the instance local status
        # to be spawning, not deleted. See LP Bug#1061167
        cls.client.wait_for_server_termination(srv['id'],
                                               ignore_error=True)
        cls.deleted_fixtures.append(srv)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('24a26f1a-1ddc-4eea-b0d7-a90cc874ad8f')
    def test_list_servers_with_a_deleted_server(self):
        # Verify deleted servers do not show by default in list servers
        # List servers and verify server not returned
        body = self.client.list_servers()
        servers = body['servers']
        deleted_ids = [s['id'] for s in self.deleted_fixtures]
        actual = [srv for srv in servers
                  if srv['id'] in deleted_ids]
        self.assertEqual([], actual)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ff01387d-c7ad-47b4-ae9e-64fa214638fe')
    def test_list_servers_by_non_existing_image(self):
        # Listing servers for a non existing image returns empty list
        non_existing_image = '1234abcd-zzz0-aaa9-ppp3-0987654abcde'
        body = self.client.list_servers(dict(image=non_existing_image))
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('5913660b-223b-44d4-a651-a0fbfd44ca75')
    def test_list_servers_by_non_existing_flavor(self):
        # Listing servers by non existing flavor returns empty list
        non_existing_flavor = 1234
        body = self.client.list_servers(dict(flavor=non_existing_flavor))
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e2c77c4a-000a-4af3-a0bd-629a328bde7c')
    def test_list_servers_by_non_existing_server_name(self):
        # Listing servers for a non existent server name returns empty list
        non_existing_name = 'junk_server_1234'
        body = self.client.list_servers(dict(name=non_existing_name))
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('fcdf192d-0f74-4d89-911f-1ec002b822c4')
    def test_list_servers_status_non_existing(self):
        # Return an empty list when invalid status is specified
        non_existing_status = 'BALONEY'
        body = self.client.list_servers(dict(status=non_existing_status))
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type='gate')
    @test.idempotent_id('12c80a9f-2dec-480e-882b-98ba15757659')
    def test_list_servers_by_limits(self):
        # List servers by specifying limits
        body = self.client.list_servers({'limit': 1})
        self.assertEqual(1, len([x for x in body['servers'] if 'id' in x]))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d47c17fb-eebd-4287-8e95-f20a7e627b18')
    def test_list_servers_by_limits_greater_than_actual_count(self):
        # List servers by specifying a greater value for limit
        body = self.client.list_servers({'limit': 100})
        self.assertEqual(len(self.existing_fixtures), len(body['servers']))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('679bc053-5e70-4514-9800-3dfab1a380a6')
    def test_list_servers_by_limits_pass_string(self):
        # Return an error if a string value is passed for limit
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          {'limit': 'testing'})

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('62610dd9-4713-4ee0-8beb-fd2c1aa7f950')
    def test_list_servers_by_limits_pass_negative_value(self):
        # Return an error if a negative value for limit is passed
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          {'limit': -1})

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('87d12517-e20a-4c9c-97b6-dd1628d6d6c9')
    def test_list_servers_by_changes_since_invalid_date(self):
        # Return an error when invalid date format is passed
        self.assertRaises(lib_exc.BadRequest, self.client.list_servers,
                          {'changes-since': '2011/01/01'})

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('74745ad8-b346-45b5-b9b8-509d7447fc1f')
    def test_list_servers_by_changes_since_future_date(self):
        # Return an empty list when a date in the future is passed
        changes_since = {'changes-since': '2051-01-01T12:34:00Z'}
        body = self.client.list_servers(changes_since)
        self.assertEqual(0, len(body['servers']))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('93055106-2d34-46fe-af68-d9ddbf7ee570')
    def test_list_servers_detail_server_is_deleted(self):
        # Server details are not listed for a deleted server
        deleted_ids = [s['id'] for s in self.deleted_fixtures]
        body = self.client.list_servers_with_detail()
        servers = body['servers']
        actual = [srv for srv in servers
                  if srv['id'] in deleted_ids]
        self.assertEqual([], actual)
