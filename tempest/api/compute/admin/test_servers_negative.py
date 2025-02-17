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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ServersAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    """Negative Tests of Servers API using admin privileges"""

    @classmethod
    def setup_clients(cls):
        super(ServersAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_admin.servers_client
        cls.quotas_client = cls.os_admin.quotas_client

    @classmethod
    def resource_setup(cls):
        super(ServersAdminNegativeTestJSON, cls).resource_setup()
        cls.tenant_id = cls.client.tenant_id

        server = cls.create_test_server(wait_until='ACTIVE')
        cls.s1_id = server['id']

    @decorators.idempotent_id('28dcec23-f807-49da-822c-56a92ea3c687')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @decorators.attr(type=['negative'])
    def test_resize_server_using_overlimit_ram(self):
        """Test resizing server using over limit ram should fail"""
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        quota_set = self.quotas_client.show_quota_set(
            self.tenant_id)['quota_set']
        ram = quota_set['ram']
        if ram == -1:
            raise self.skipException("ram quota set is -1,"
                                     " cannot test overlimit")
        ram += 1
        vcpus = 1
        disk = 5
        flavor_ref = self.create_flavor(ram=ram, vcpus=vcpus, disk=disk)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.client.resize_server,
                          self.s1_id,
                          flavor_ref['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7fcadfab-bd6a-4753-8db7-4a51e51aade9')
    def test_restore_server_invalid_state(self):
        """Restore-deleting a server not in 'soft-delete' state should fail

        We can restore a soft deleted server, but can't restore a server that
        is not in 'soft-delete' state.
        """
        self.assertRaises(lib_exc.Conflict,
                          self.client.restore_soft_deleted_server,
                          self.s1_id)

    @decorators.idempotent_id('7368a427-2f26-4ad9-9ba9-911a0ec2b0db')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @decorators.attr(type=['negative'])
    def test_resize_server_using_overlimit_vcpus(self):
        """Test resizing server using over limit vcpus should fail"""
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        quota_set = self.quotas_client.show_quota_set(
            self.tenant_id)['quota_set']
        vcpus = quota_set['cores']
        if vcpus == -1:
            raise self.skipException("cores quota set is -1,"
                                     " cannot test overlimit")
        vcpus += 1
        ram = 512
        disk = 5
        flavor_ref = self.create_flavor(ram=ram, vcpus=vcpus, disk=disk)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.client.resize_server,
                          self.s1_id,
                          flavor_ref['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b0b4d8af-1256-41ef-9ee7-25f1c19dde80')
    def test_reset_state_server_invalid_state(self):
        """Test resetting server state to invalid state value should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state='invalid')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4cdcc984-fab0-4577-9a9d-6d558527ee9d')
    def test_reset_state_server_invalid_type(self):
        """Test resetting server state to invalid state type should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state=1)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e741298b-8df2-46f0-81cb-8f814ff2504c')
    def test_reset_state_server_nonexistent_server(self):
        """Test resetting a non existent server's state should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.reset_state, '999', state='error')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('46a4e1ca-87ae-4d28-987a-1b6b136a0221')
    def test_migrate_non_existent_server(self):
        """Test migrating a non existent server should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.migrate_server,
                          data_utils.rand_uuid())

    @decorators.idempotent_id('b0b17f83-d14e-4fc4-8f31-bcc9f3cfa629')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration not available.')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type=['negative'])
    def test_migrate_server_invalid_state(self):
        """Test migrating a server with invalid state should fail"""
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
