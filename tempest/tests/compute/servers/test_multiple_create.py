# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp
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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base


class MultipleCreateTestJSON(base.BaseComputeTest):
    _interface = 'json'
    _name = 'multiple-create-test'

    def _get_created_servers(self, name):
        """Get servers created which name match with name param."""
        resp, body = self.servers_client.list_servers()
        servers = body['servers']
        servers_created = []
        for server in servers:
            if server['name'].startswith(name):
                servers_created.append(server)
        return servers_created

    def _generate_name(self):
        return rand_name(self._name)

    def _create_multiple_servers(self, name=None, wait_until=None, **kwargs):
        """
        This is the right way to create_multiple servers and manage to get the
        created servers into the servers list to be cleaned up after all.
        """
        kwargs['name'] = kwargs.get('name', self._generate_name())
        resp, body = self.create_server(**kwargs)
        created_servers = self._get_created_servers(kwargs['name'])
        # NOTE(maurosr): append it to cls.servers list from base.BaseCompute
        # class.
        self.servers.append(created_servers)
        # NOTE(maurosr): get a server list, check status of the ones with names
        # that match and wait for them become active. At a first look, since
        # they are building in parallel, wait inside the for doesn't seem be
        # harmful to the performance
        if wait_until is not None:
            for server in created_servers:
                self.servers_client.wait_for_server_status(server['id'],
                                                           wait_until)

        return resp, body

    @attr(type='positive')
    def test_multiple_create(self):
        resp, body = self._create_multiple_servers(wait_until='ACTIVE',
                                                   min_count=1,
                                                   max_count=2)
        # NOTE(maurosr): do status response check and also make sure that
        # reservation_id is not in the response body when the request send
        # contains return_reservation_id=False
        self.assertEqual('202', resp['status'])
        self.assertFalse('reservation_id' in body)

    @attr(type='negative')
    def test_min_count_less_than_one(self):
        invalid_min_count = 0
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @attr(type='negative')
    def test_min_count_non_integer(self):
        invalid_min_count = 2.5
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @attr(type='negative')
    def test_max_count_less_than_one(self):
        invalid_max_count = 0
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @attr(type='negative')
    def test_max_count_non_integer(self):
        invalid_max_count = 2.5
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @attr(type='negative')
    def test_max_count_less_than_min_count(self):
        min_count = 3
        max_count = 2
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=min_count,
                          max_count=max_count)

    @attr(type='positive')
    def test_multiple_create_with_reservation_return(self):
        resp, body = self._create_multiple_servers(wait_until='ACTIVE',
                                                   min_count=1,
                                                   max_count=2,
                                                   return_reservation_id=True)
        self.assertTrue(resp['status'], 202)
        self.assertIn('reservation_id', body)


class MultipleCreateTestXML(MultipleCreateTestJSON):
    _interface = 'xml'
