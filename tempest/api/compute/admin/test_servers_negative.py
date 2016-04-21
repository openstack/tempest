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

import testtools

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class ServersAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Servers API using admin privileges"""

    @classmethod
    def setup_clients(cls):
        super(ServersAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.servers_client
        cls.non_adm_client = cls.servers_client
        cls.flavors_client = cls.os_adm.flavors_client

    @classmethod
    def resource_setup(cls):
        super(ServersAdminNegativeTestJSON, cls).resource_setup()
        cls.tenant_id = cls.client.tenant_id

        cls.s1_name = data_utils.rand_name('server')
        server = cls.create_test_server(name=cls.s1_name,
                                        wait_until='ACTIVE')
        cls.s1_id = server['id']

    def _get_unused_flavor_id(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        while True:
            try:
                self.flavors_client.show_flavor(flavor_id)
            except lib_exc.NotFound:
                break
            flavor_id = data_utils.rand_int_id(start=1000)
        return flavor_id

    @test.idempotent_id('28dcec23-f807-49da-822c-56a92ea3c687')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type=['negative'])
    def test_resize_server_using_overlimit_ram(self):
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        flavor_name = data_utils.rand_name("flavor")
        flavor_id = self._get_unused_flavor_id()
        quota_set = (self.quotas_client.show_default_quota_set(self.tenant_id)
                     ['quota_set'])
        ram = int(quota_set['ram'])
        if ram == -1:
            raise self.skipException("default ram quota set is -1,"
                                     " cannot test overlimit")
        ram += 1
        vcpus = 8
        disk = 10
        flavor_ref = self.flavors_client.create_flavor(name=flavor_name,
                                                       ram=ram, vcpus=vcpus,
                                                       disk=disk,
                                                       id=flavor_id)['flavor']
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.client.resize_server,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @test.idempotent_id('7368a427-2f26-4ad9-9ba9-911a0ec2b0db')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type=['negative'])
    def test_resize_server_using_overlimit_vcpus(self):
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        flavor_name = data_utils.rand_name("flavor")
        flavor_id = self._get_unused_flavor_id()
        ram = 512
        quota_set = (self.quotas_client.show_default_quota_set(self.tenant_id)
                     ['quota_set'])
        vcpus = int(quota_set['cores'])
        if vcpus == -1:
            raise self.skipException("default cores quota set is -1,"
                                     " cannot test overlimit")
        vcpus += 1
        disk = 10
        flavor_ref = self.flavors_client.create_flavor(name=flavor_name,
                                                       ram=ram, vcpus=vcpus,
                                                       disk=disk,
                                                       id=flavor_id)['flavor']
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.client.resize_server,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('b0b4d8af-1256-41ef-9ee7-25f1c19dde80')
    def test_reset_state_server_invalid_state(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state='invalid')

    @test.attr(type=['negative'])
    @test.idempotent_id('4cdcc984-fab0-4577-9a9d-6d558527ee9d')
    def test_reset_state_server_invalid_type(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state=1)

    @test.attr(type=['negative'])
    @test.idempotent_id('e741298b-8df2-46f0-81cb-8f814ff2504c')
    def test_reset_state_server_nonexistent_server(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.reset_state, '999', state='error')

    @test.attr(type=['negative'])
    @test.idempotent_id('e84e2234-60d2-42fa-8b30-e2d3049724ac')
    def test_get_server_diagnostics_by_non_admin(self):
        # Non-admin user can not view server diagnostics according to policy
        self.assertRaises(lib_exc.Forbidden,
                          self.non_adm_client.show_server_diagnostics,
                          self.s1_id)

    @test.attr(type=['negative'])
    @test.idempotent_id('46a4e1ca-87ae-4d28-987a-1b6b136a0221')
    def test_migrate_non_existent_server(self):
        # migrate a non existent server
        self.assertRaises(lib_exc.NotFound,
                          self.client.migrate_server,
                          data_utils.rand_uuid())

    @test.idempotent_id('b0b17f83-d14e-4fc4-8f31-bcc9f3cfa629')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.attr(type=['negative'])
    def test_migrate_server_invalid_state(self):
        # create server.
        server = self.create_test_server(wait_until='ACTIVE')
        server_id = server['id']
        # suspend the server.
        self.client.suspend_server(server_id)
        waiters.wait_for_server_status(self.client,
                                       server_id, 'SUSPENDED')
        # migrate a suspended server should fail
        self.assertRaises(lib_exc.Conflict,
                          self.client.migrate_server,
                          server_id)
