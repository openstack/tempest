# Copyright 2013 Huawei Technologies Co.,LTD.
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

import uuid

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class ServersAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Servers API using admin privileges
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServersAdminNegativeTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.servers_client
        cls.non_adm_client = cls.servers_client
        cls.flavors_client = cls.os_adm.flavors_client
        cls.identity_client = cls._get_identity_admin_client()
        tenant = cls.identity_client.get_tenant_by_name(
            cls.client.tenant_name)
        cls.tenant_id = tenant['id']

        cls.s1_name = data_utils.rand_name('server')
        resp, server = cls.create_test_server(name=cls.s1_name,
                                              wait_until='ACTIVE')
        cls.s1_id = server['id']

    def _get_unused_flavor_id(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        while True:
            try:
                resp, body = self.flavors_client.get_flavor_details(flavor_id)
            except exceptions.NotFound:
                break
            flavor_id = data_utils.rand_int_id(start=1000)
        return flavor_id

    @attr(type=['negative', 'gate'])
    def test_resize_server_using_overlimit_ram(self):
        flavor_name = data_utils.rand_name("flavor-")
        flavor_id = self._get_unused_flavor_id()
        resp, quota_set = self.quotas_client.get_default_quota_set(
            self.tenant_id)
        ram = int(quota_set['ram']) + 1
        vcpus = 8
        disk = 10
        resp, flavor_ref = self.flavors_client.create_flavor(flavor_name,
                                                             ram, vcpus, disk,
                                                             flavor_id)
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises(exceptions.OverLimit,
                          self.client.resize,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @attr(type=['negative', 'gate'])
    def test_resize_server_using_overlimit_vcpus(self):
        flavor_name = data_utils.rand_name("flavor-")
        flavor_id = self._get_unused_flavor_id()
        ram = 512
        resp, quota_set = self.quotas_client.get_default_quota_set(
            self.tenant_id)
        vcpus = int(quota_set['cores']) + 1
        disk = 10
        resp, flavor_ref = self.flavors_client.create_flavor(flavor_name,
                                                             ram, vcpus, disk,
                                                             flavor_id)
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises(exceptions.OverLimit,
                          self.client.resize,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_invalid_state(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state='invalid')

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_invalid_type(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state=1)

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_nonexistent_server(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.reset_state, '999')

    @attr(type=['negative', 'gate'])
    def test_get_server_diagnostics_by_non_admin(self):
        # Non-admin user can not view server diagnostics according to policy
        self.assertRaises(exceptions.Unauthorized,
                          self.non_adm_client.get_server_diagnostics,
                          self.s1_id)

    @attr(type=['negative', 'gate'])
    def test_migrate_non_existent_server(self):
        # migrate a non existent server
        self.assertRaises(exceptions.NotFound,
                          self.client.migrate_server,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_migrate_server_invalid_state(self):
        # create server.
        resp, server = self.create_test_server(wait_until='ACTIVE')
        self.assertEqual(202, resp.status)
        server_id = server['id']
        # suspend the server.
        resp, _ = self.client.suspend_server(server_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(server_id, 'SUSPENDED')
        # migrate an suspended server should fail
        self.assertRaises(exceptions.Conflict,
                          self.client.migrate_server,
                          server_id)


class ServersAdminNegativeTestXML(ServersAdminNegativeTestJSON):
    _interface = 'xml'
