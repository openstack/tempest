# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

from tempest.api.volume import base
from tempest.common import identity
from tempest.common import tempest_fixtures as fixtures
from tempest.common import waiters
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes', 'backups',
              'backup_gigabytes', 'per_volume_gigabytes']
QUOTA_USAGE_KEYS = ['reserved', 'limit', 'in_use']


class BaseVolumeQuotasAdminTestJSON(base.BaseVolumeAdminTest):
    force_tenant_isolation = True

    credentials = ['primary', 'alt', 'admin']

    def setUp(self):
        # NOTE(jeremy.zhang): Avoid conflicts with volume quota class tests.
        self.useFixture(fixtures.LockFixture('volume_quotas'))
        super(BaseVolumeQuotasAdminTestJSON, self).setUp()

    @classmethod
    def setup_credentials(cls):
        super(BaseVolumeQuotasAdminTestJSON, cls).setup_credentials()
        cls.demo_tenant_id = cls.os_primary.credentials.tenant_id

    @classmethod
    def setup_clients(cls):
        super(BaseVolumeQuotasAdminTestJSON, cls).setup_clients()
        cls.transfer_client = cls.os_primary.volume_transfers_v2_client
        cls.alt_transfer_client = cls.os_alt.volume_transfers_v2_client

    @decorators.idempotent_id('59eada70-403c-4cef-a2a3-a8ce2f1b07a0')
    def test_list_quotas(self):
        quotas = (self.admin_quotas_client.show_quota_set(self.demo_tenant_id)
                  ['quota_set'])
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @decorators.idempotent_id('2be020a2-5fdd-423d-8d35-a7ffbc36e9f7')
    def test_list_default_quotas(self):
        quotas = self.admin_quotas_client.show_default_quota_set(
            self.demo_tenant_id)['quota_set']
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @decorators.idempotent_id('3d45c99e-cc42-4424-a56e-5cbd212b63a6')
    def test_update_all_quota_resources_for_tenant(self):
        # Admin can update all the resource quota limits for a tenant
        default_quota_set = self.admin_quotas_client.show_default_quota_set(
            self.demo_tenant_id)['quota_set']
        new_quota_set = {'gigabytes': 1009,
                         'volumes': 11,
                         'snapshots': 11,
                         'backups': 11,
                         'backup_gigabytes': 1009,
                         'per_volume_gigabytes': 1009}

        # Update limits for all quota resources
        quota_set = self.admin_quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)['quota_set']

        cleanup_quota_set = dict(
            (k, v) for k, v in default_quota_set.items()
            if k in QUOTA_KEYS)
        self.addCleanup(self.admin_quotas_client.update_quota_set,
                        self.demo_tenant_id, **cleanup_quota_set)
        # test that the specific values we set are actually in
        # the final result. There is nothing here that ensures there
        # would be no other values in there.
        self.assertDictContainsSubset(new_quota_set, quota_set)

    @decorators.idempotent_id('18c51ae9-cb03-48fc-b234-14a19374dbed')
    def test_show_quota_usage(self):
        quota_usage = self.admin_quotas_client.show_quota_set(
            self.os_admin.credentials.tenant_id,
            params={'usage': True})['quota_set']
        for key in QUOTA_KEYS:
            self.assertIn(key, quota_usage)
            for usage_key in QUOTA_USAGE_KEYS:
                self.assertIn(usage_key, quota_usage[key])

    @decorators.idempotent_id('ae8b6091-48ad-4bfa-a188-bbf5cc02115f')
    def test_quota_usage(self):
        quota_usage = self.admin_quotas_client.show_quota_set(
            self.demo_tenant_id, params={'usage': True})['quota_set']

        volume = self.create_volume()
        self.addCleanup(self.delete_volume,
                        self.volumes_client, volume['id'])

        new_quota_usage = self.admin_quotas_client.show_quota_set(
            self.demo_tenant_id, params={'usage': True})['quota_set']

        self.assertEqual(quota_usage['volumes']['in_use'] + 1,
                         new_quota_usage['volumes']['in_use'])

        self.assertEqual(quota_usage['gigabytes']['in_use'] +
                         volume["size"],
                         new_quota_usage['gigabytes']['in_use'])

    @decorators.idempotent_id('874b35a9-51f1-4258-bec5-cd561b6690d3')
    def test_delete_quota(self):
        # Admin can delete the resource quota set for a project
        project_name = data_utils.rand_name('quota_tenant')
        description = data_utils.rand_name('desc_')
        project = identity.identity_utils(self.os_admin).create_project(
            project_name, description=description)
        project_id = project['id']
        self.addCleanup(identity.identity_utils(self.os_admin).delete_project,
                        project_id)
        quota_set_default = self.admin_quotas_client.show_default_quota_set(
            project_id)['quota_set']
        volume_default = quota_set_default['volumes']

        self.admin_quotas_client.update_quota_set(
            project_id, volumes=(volume_default + 5))

        self.admin_quotas_client.delete_quota_set(project_id)
        quota_set_new = (self.admin_quotas_client.show_quota_set(project_id)
                         ['quota_set'])
        self.assertEqual(volume_default, quota_set_new['volumes'])

    @decorators.idempotent_id('8911036f-9d54-4720-80cc-a1c9796a8805')
    def test_quota_usage_after_volume_transfer(self):
        # Create a volume for transfer
        volume = self.create_volume()
        self.addCleanup(self.delete_volume,
                        self.admin_volume_client, volume['id'])

        # List of tenants quota usage pre-transfer
        primary_quota = self.admin_quotas_client.show_quota_set(
            self.demo_tenant_id, params={'usage': True})['quota_set']

        alt_quota = self.admin_quotas_client.show_quota_set(
            self.os_alt.volumes_client_latest.tenant_id,
            params={'usage': True})['quota_set']

        # Creates a volume transfer
        transfer = self.transfer_client.create_volume_transfer(
            volume_id=volume['id'])['transfer']
        transfer_id = transfer['id']
        auth_key = transfer['auth_key']

        # Accepts a volume transfer
        self.alt_transfer_client.accept_volume_transfer(
            transfer_id, auth_key=auth_key)

        # Verify volume transferred is available
        waiters.wait_for_volume_resource_status(
            self.os_alt.volumes_client_latest, volume['id'], 'available')

        # List of tenants quota usage post transfer
        new_primary_quota = self.admin_quotas_client.show_quota_set(
            self.demo_tenant_id, params={'usage': True})['quota_set']

        new_alt_quota = self.admin_quotas_client.show_quota_set(
            self.os_alt.volumes_client_latest.tenant_id,
            params={'usage': True})['quota_set']

        # Verify tenants quota usage was updated
        self.assertEqual(primary_quota['volumes']['in_use'] -
                         new_primary_quota['volumes']['in_use'],
                         new_alt_quota['volumes']['in_use'] -
                         alt_quota['volumes']['in_use'])

        self.assertEqual(alt_quota['gigabytes']['in_use'] +
                         volume['size'],
                         new_alt_quota['gigabytes']['in_use'])

        self.assertEqual(primary_quota['gigabytes']['in_use'] -
                         volume['size'],
                         new_primary_quota['gigabytes']['in_use'])
