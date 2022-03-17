# Copyright 2021 Red Hat, Inc.
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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.scenario import manager

CONF = config.CONF


class ComputeProjectQuotaTest(manager.ScenarioTest):
    """The test base class for compute unified limits tests.

    Dynamic credentials (unique tenants) are created on a per-class basis, so
    we test different quota limits in separate test classes to prevent a quota
    limit update in one test class from affecting a test running in another
    test class in parallel.

    https://docs.openstack.org/tempest/latest/configuration.html#dynamic-credentials
    """
    credentials = ['primary', 'system_admin']
    force_tenant_isolation = True

    @classmethod
    def skip_checks(cls):
        super(ComputeProjectQuotaTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.unified_limits:
            raise cls.skipException('Compute unified limits are not enabled.')

    @classmethod
    def resource_setup(cls):
        super(ComputeProjectQuotaTest, cls).resource_setup()

        # Figure out and record the nova service id
        services = cls.os_system_admin.identity_services_v3_client.\
            list_services()
        nova_services = [x for x in services['services']
                         if x['name'] == 'nova']
        cls.nova_service_id = nova_services[0]['id']

        # Pre-create quota limits in subclasses and record their IDs so we can
        # update them in-place without needing to know which ones have been
        # created and in which order.
        cls.limit_ids = {}

    @classmethod
    def _create_limit(cls, name, value):
        return cls.os_system_admin.identity_limits_client.create_limit(
            CONF.identity.region, cls.nova_service_id,
            cls.servers_client.tenant_id, name, value)['limits'][0]['id']

    def _update_limit(self, name, value):
        self.os_system_admin.identity_limits_client.update_limit(
            self.limit_ids[name], value)


class ServersQuotaTest(ComputeProjectQuotaTest):

    @classmethod
    def resource_setup(cls):
        super(ServersQuotaTest, cls).resource_setup()

        try:
            cls.limit_ids['servers'] = cls._create_limit(
                'servers', 5)
            cls.limit_ids['class:VCPU'] = cls._create_limit(
                'class:VCPU', 10)
            cls.limit_ids['class:MEMORY_MB'] = cls._create_limit(
                'class:MEMORY_MB', 25 * 1024)
            cls.limit_ids['class:DISK_GB'] = cls._create_limit(
                'class:DISK_GB', 10)
        except lib_exc.Forbidden:
            raise cls.skipException('Target system is not configured with '
                                    'compute unified limits')

    @decorators.idempotent_id('555d8bbf-d2ed-4e39-858c-4235899402d9')
    @utils.services('compute')
    def test_server_count_vcpu_memory_disk_quota(self):
        # Set a quota on the number of servers for our tenant to one.
        self._update_limit('servers', 1)

        # Create one server.
        first = self.create_server(name='first')

        # Second server would put us over quota, so expect failure.
        # NOTE: In nova, quota exceeded raises 403 Forbidden.
        self.assertRaises(lib_exc.Forbidden,
                          self.create_server,
                          name='second')

        # Update our limit to two.
        self._update_limit('servers', 2)

        # Now the same create should succeed.
        second = self.create_server(name='second')

        # Third server would put us over quota, so expect failure.
        self.assertRaises(lib_exc.Forbidden,
                          self.create_server,
                          name='third')

        # Delete the first server to put us under quota.
        self.servers_client.delete_server(first['id'])
        waiters.wait_for_server_termination(self.servers_client, first['id'])

        # Now the same create should succeed.
        third = self.create_server(name='third')

        # Set the servers limit back to 10 to test other resources.
        self._update_limit('servers', 10)

        # Default flavor has: VCPU=1, MEMORY_MB=512, DISK_GB=1
        # We are currently using 2 VCPU, set the limit to 2.
        self._update_limit('class:VCPU', 2)

        # Server create should fail as it would go over quota.
        self.assertRaises(lib_exc.Forbidden,
                          self.create_server,
                          name='fourth')

        # Delete the second server to put us under quota.
        self.servers_client.delete_server(second['id'])
        waiters.wait_for_server_termination(self.servers_client, second['id'])

        # Same create should now succeed.
        fourth = self.create_server(name='fourth')

        # We are currently using 2 DISK_GB. Set limit to 1.
        self._update_limit('class:DISK_GB', 1)

        # Server create should fail because we're already over (new) quota.
        self.assertRaises(lib_exc.Forbidden,
                          self.create_server,
                          name='fifth')

        # Delete the third server.
        self.servers_client.delete_server(third['id'])
        waiters.wait_for_server_termination(self.servers_client, third['id'])

        # Server create should fail again because it would still put us over
        # quota.
        self.assertRaises(lib_exc.Forbidden,
                          self.create_server,
                          name='fifth')

        # Delete the fourth server.
        self.servers_client.delete_server(fourth['id'])
        waiters.wait_for_server_termination(self.servers_client, fourth['id'])

        # Server create should succeed now.
        self.create_server(name='fifth')
