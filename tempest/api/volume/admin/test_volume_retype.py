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

import abc

from oslo_log import log as logging
import testtools

from tempest.api.volume import base
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF

LOG = logging.getLogger(__name__)


class VolumeRetypeTest(base.BaseVolumeAdminTest):

    def _wait_for_internal_volume_cleanup(self, vol):
        # When retyping a volume, Cinder creates an internal volume in the
        # target backend. The volume in the source backend is deleted after
        # the migration, so we need to wait for Cinder delete this volume
        # before deleting the types we've created.

        # This list should return 2 volumes until the copy and cleanup
        # process is finished.
        fetched_list = self.admin_volume_client.list_volumes(
            params={'all_tenants': True,
                    'name': vol['name']})['volumes']

        for fetched_vol in fetched_list:
            if fetched_vol['id'] != vol['id']:
                # This is the Cinder internal volume
                LOG.debug('Waiting for internal volume %s deletion',
                          fetched_vol['id'])
                self.admin_volume_client.wait_for_resource_deletion(
                    fetched_vol['id'])
                break

    @abc.abstractmethod
    def _verify_migration(self, source_vol, dest_vol):
        pass

    def _create_volume_from_snapshot(self):
        # Create a volume in the first backend
        src_vol = self.create_volume(volume_type=self.src_vol_type['name'])

        # Create a volume snapshot
        snapshot = self.create_snapshot(src_vol['id'])

        # Create a volume from the snapshot
        src_vol = self.create_volume(volume_type=self.src_vol_type['name'],
                                     snapshot_id=snapshot['id'])

        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])

        return src_vol

    def _retype_volume(self, volume, migration_policy):

        volume_source = self.admin_volume_client.show_volume(
            volume['id'])['volume']

        self.volumes_client.retype_volume(
            volume['id'],
            new_type=self.dst_vol_type['name'],
            migration_policy=migration_policy)
        self.addCleanup(self._wait_for_internal_volume_cleanup, volume)
        waiters.wait_for_volume_retype(self.volumes_client, volume['id'],
                                       self.dst_vol_type['name'])

        volume_dest = self.admin_volume_client.show_volume(
            volume['id'])['volume']

        self._verify_migration(volume_source, volume_dest)


class VolumeRetypeWithMigrationTest(VolumeRetypeTest):
    """Test volume retype with migration"""

    @classmethod
    def skip_checks(cls):
        super(VolumeRetypeTest, cls).skip_checks()

        if not CONF.volume_feature_enabled.multi_backend:
            raise cls.skipException("Cinder multi-backend feature disabled")

        if len(set(CONF.volume.backend_names)) < 2:
            raise cls.skipException("Requires at least two different "
                                    "backend names")

    @classmethod
    def resource_setup(cls):
        super(VolumeRetypeWithMigrationTest, cls).resource_setup()
        # read backend name from a list.
        backend_src = CONF.volume.backend_names[0]
        backend_dst = CONF.volume.backend_names[1]

        extra_specs_src = {"volume_backend_name": backend_src}
        extra_specs_dst = {"volume_backend_name": backend_dst}

        cls.src_vol_type = cls.create_volume_type(extra_specs=extra_specs_src)
        cls.dst_vol_type = cls.create_volume_type(extra_specs=extra_specs_dst)

    def _verify_migration(self, volume_source, volume_dest):

        keys_with_no_change = ('id', 'size', 'description', 'name',
                               'user_id', 'os-vol-tenant-attr:tenant_id')
        keys_with_change = ('volume_type', 'os-vol-host-attr:host')

        # Check the volume information after the migration.
        self.assertEqual('success',
                         volume_dest['os-vol-mig-status-attr:migstat'])
        self.assertEqual('success', volume_dest['migration_status'])

        for key in keys_with_no_change:
            self.assertEqual(volume_source[key], volume_dest[key])

        for key in keys_with_change:
            self.assertNotEqual(volume_source[key], volume_dest[key])

        self.assertEqual(volume_dest['volume_type'], self.dst_vol_type['name'])

    @decorators.idempotent_id('a1a41f3f-9dad-493e-9f09-3ff197d477cd')
    def test_available_volume_retype_with_migration(self):
        """Test volume retype with migration

        1. Create volume1 with volume_type1
        2. Retype volume1 to volume_type2 with migration_policy='on-demand'
        3. Check volume1's volume_type is changed to volume_type2, and
           'os-vol-host-attr:host' in the volume info is changed.
        """
        src_vol = self.create_volume(volume_type=self.src_vol_type['name'])
        self._retype_volume(src_vol, migration_policy='on-demand')

    @decorators.idempotent_id('d0d9554f-e7a5-4104-8973-f35b27ccb60d')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          "Cinder volume snapshots are disabled.")
    def test_volume_from_snapshot_retype_with_migration(self):
        """Test volume created from snapshot retype with migration

        1. Create volume1 from snapshot with volume_type1
        2. Retype volume1 to volume_type2 with migration_policy='on-demand'
        3. Check volume1's volume_type is changed to volume_type2, and
           'os-vol-host-attr:host' in the volume info is changed.
        """
        src_vol = self._create_volume_from_snapshot()

        # Migrate the volume from snapshot to the second backend
        self._retype_volume(src_vol, migration_policy='on-demand')


class VolumeRetypeWithoutMigrationTest(VolumeRetypeTest):
    """Test volume retype without migration"""

    @classmethod
    def resource_setup(cls):
        super(VolumeRetypeWithoutMigrationTest, cls).resource_setup()
        cls.src_vol_type = cls.create_volume_type('volume-type-1')
        cls.dst_vol_type = cls.create_volume_type('volume-type-2')

    def _verify_migration(self, volume_source, volume_dest):

        keys_with_no_change = ('id', 'size', 'description', 'name',
                               'user_id', 'os-vol-tenant-attr:tenant_id',
                               'os-vol-host-attr:host')
        keys_with_change = ('volume_type',)

        # Check the volume information after the retype
        self.assertIsNone(volume_dest['os-vol-mig-status-attr:migstat'])
        self.assertIsNone(volume_dest['migration_status'])

        for key in keys_with_no_change:
            self.assertEqual(volume_source[key], volume_dest[key])

        for key in keys_with_change:
            self.assertNotEqual(volume_source[key], volume_dest[key])

        self.assertEqual(volume_dest['volume_type'], self.dst_vol_type['name'])

    @decorators.idempotent_id('b90412ee-465d-46e9-b249-ec84a47d5f25')
    def test_available_volume_retype(self):
        """Test volume retype without migration

        1. Create volume1 with volume_type1
        2. Retype volume1 to volume_type2 with migration_policy='never'
        3. Check volume1's volume_type is changed to volume_type2, and
           'os-vol-host-attr:host' in the volume info is not changed.
        """
        src_vol = self.create_volume(volume_type=self.src_vol_type['name'])

        # Retype the volume from snapshot
        self._retype_volume(src_vol, migration_policy='never')


class VolumeRetypeMultiattachTest(VolumeRetypeTest):
    """Test volume retype with/without multiattach"""

    volume_min_microversion = '3.50'
    volume_max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(VolumeRetypeMultiattachTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.volume_multiattach:
            raise cls.skipException('Volume multi-attach is not available.')

    @classmethod
    def resource_setup(cls):
        super(VolumeRetypeMultiattachTest, cls).resource_setup()
        extra_specs_src = {"multiattach": '<is> True'}
        cls.src_vol_type = cls.create_volume_type()
        cls.dst_vol_type = cls.create_volume_type(extra_specs=extra_specs_src)

    def _verify_migration(self, source_vol, dest_vol):
        self.assertEqual(dest_vol['status'], "available")
        self.assertEqual(dest_vol['volume_type'], self.dst_vol_type['name'])
        if "multiattach" in self.dst_vol_type['extra_specs'].keys():
            self.assertEqual(dest_vol['multiattach'], True)
        else:
            self.assertEqual(dest_vol['multiattach'], False)

    @decorators.idempotent_id('c0521465-ed82-4d03-961d-a68d673a5051')
    def test_volume_retype_multiattach(self):
        """Test volume retype with/without multiattach

        1. Create dst_vol_type with "multiattach = '<is> True'"
        2. Create src_vol_type without the "multiattach" property
        3. Retype volume from src_vol_type (non-multiattach)
           to dst_vol_type(multiattach) and vice versa
        4. Verify successful retype.
        """
        # Retype from non-multiattach to multiattach
        vol = self.create_volume(volume_type=self.src_vol_type['name'])
        self._retype_volume(vol, migration_policy='never')

        self.dst_vol_type = self.src_vol_type

        # Retype from multiattach to non-multiattach
        self._retype_volume(vol, migration_policy='never')
