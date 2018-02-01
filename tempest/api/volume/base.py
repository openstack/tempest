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

from tempest.api.volume import api_microversion_fixture
from tempest.common import compute
from tempest.common import waiters
from tempest import config
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
import tempest.test

CONF = config.CONF


class BaseVolumeTest(api_version_utils.BaseMicroversionTest,
                     tempest.test.BaseTestCase):
    """Base test case class for all Cinder API tests."""

    _api_version = 2
    # if api_v2 is not enabled while api_v3 is enabled, the volume v2 classes
    # should be transferred to volume v3 classes.
    if (not CONF.volume_feature_enabled.api_v2 and
        CONF.volume_feature_enabled.api_v3):
        _api_version = 3
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseVolumeTest, cls).skip_checks()

        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if cls._api_version == 2:
            if not CONF.volume_feature_enabled.api_v2:
                msg = "Volume API v2 is disabled"
                raise cls.skipException(msg)
        elif cls._api_version == 3:
            if not CONF.volume_feature_enabled.api_v3:
                msg = "Volume API v3 is disabled"
                raise cls.skipException(msg)
        else:
            msg = ("Invalid Cinder API version (%s)" % cls._api_version)
            raise exceptions.InvalidConfiguration(msg)

        api_version_utils.check_skip_with_microversion(
            cls.min_microversion, cls.max_microversion,
            CONF.volume.min_microversion, CONF.volume.max_microversion)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseVolumeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseVolumeTest, cls).setup_clients()
        cls.servers_client = cls.os_primary.servers_client

        if CONF.service_available.glance:
            cls.images_client = cls.os_primary.image_client_v2

        if cls._api_version == 3:
            cls.backups_client = cls.os_primary.backups_v3_client
            cls.volumes_client = cls.os_primary.volumes_v3_client
            cls.messages_client = cls.os_primary.volume_v3_messages_client
            cls.versions_client = cls.os_primary.volume_v3_versions_client
            cls.groups_client = cls.os_primary.groups_v3_client
            cls.group_snapshots_client = (
                cls.os_primary.group_snapshots_v3_client)
        else:
            cls.backups_client = cls.os_primary.backups_v2_client
            cls.volumes_client = cls.os_primary.volumes_v2_client

        cls.snapshots_client = cls.os_primary.snapshots_v2_client
        cls.volumes_extension_client =\
            cls.os_primary.volumes_v2_extension_client
        cls.availability_zone_client = (
            cls.os_primary.volume_v2_availability_zone_client)
        cls.volume_limits_client = cls.os_primary.volume_v2_limits_client

    def setUp(self):
        super(BaseVolumeTest, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            self.request_microversion))

    @classmethod
    def resource_setup(cls):
        super(BaseVolumeTest, cls).resource_setup()
        cls.request_microversion = (
            api_version_utils.select_request_microversion(
                cls.min_microversion,
                CONF.volume.min_microversion))

        cls.image_ref = CONF.compute.image_ref
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.build_interval = CONF.volume.build_interval
        cls.build_timeout = CONF.volume.build_timeout

    @classmethod
    def create_volume(cls, wait_until='available', **kwargs):
        """Wrapper utility that returns a test volume.

           :param wait_until: wait till volume status.
        """
        if 'size' not in kwargs:
            kwargs['size'] = CONF.volume.volume_size

        if 'imageRef' in kwargs:
            image = cls.images_client.show_image(kwargs['imageRef'])
            min_disk = image['min_disk']
            kwargs['size'] = max(kwargs['size'], min_disk)

        if 'name' not in kwargs:
            name = data_utils.rand_name(cls.__name__ + '-Volume')
            kwargs['name'] = name

        volume = cls.volumes_client.create_volume(**kwargs)['volume']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.delete_volume, cls.volumes_client,
                                    volume['id'])
        waiters.wait_for_volume_resource_status(cls.volumes_client,
                                                volume['id'], wait_until)
        return volume

    @classmethod
    def create_snapshot(cls, volume_id=1, **kwargs):
        """Wrapper utility that returns a test snapshot."""
        if 'name' not in kwargs:
            name = data_utils.rand_name(cls.__name__ + '-Snapshot')
            kwargs['name'] = name

        snapshot = cls.snapshots_client.create_snapshot(
            volume_id=volume_id, **kwargs)['snapshot']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.delete_snapshot, snapshot['id'])
        waiters.wait_for_volume_resource_status(cls.snapshots_client,
                                                snapshot['id'], 'available')
        return snapshot

    def create_backup(self, volume_id, backup_client=None, **kwargs):
        """Wrapper utility that returns a test backup."""
        if backup_client is None:
            backup_client = self.backups_client
        if 'name' not in kwargs:
            name = data_utils.rand_name(self.__class__.__name__ + '-Backup')
            kwargs['name'] = name

        backup = backup_client.create_backup(
            volume_id=volume_id, **kwargs)['backup']
        self.addCleanup(backup_client.delete_backup, backup['id'])
        waiters.wait_for_volume_resource_status(backup_client, backup['id'],
                                                'available')
        return backup

    # NOTE(afazekas): these create_* and clean_* could be defined
    # only in a single location in the source, and could be more general.

    @staticmethod
    def delete_volume(client, volume_id):
        """Delete volume by the given client"""
        client.delete_volume(volume_id)
        client.wait_for_resource_deletion(volume_id)

    @classmethod
    def delete_snapshot(cls, snapshot_id, snapshots_client=None):
        """Delete snapshot by the given client"""
        if snapshots_client is None:
            snapshots_client = cls.snapshots_client
        snapshots_client.delete_snapshot(snapshot_id)
        snapshots_client.wait_for_resource_deletion(snapshot_id)

    def attach_volume(self, server_id, volume_id):
        """Attach a volume to a server"""
        self.servers_client.attach_volume(
            server_id, volumeId=volume_id,
            device='/dev/%s' % CONF.compute.volume_device_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume_id, 'in-use')
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.volumes_client, volume_id, 'available')
        self.addCleanup(self.servers_client.detach_volume, server_id,
                        volume_id)

    def create_server(self, wait_until='ACTIVE', **kwargs):
        name = kwargs.pop(
            'name',
            data_utils.rand_name(self.__class__.__name__ + '-instance'))

        tenant_network = self.get_tenant_network()
        body, _ = compute.create_test_server(
            self.os_primary,
            tenant_network=tenant_network,
            name=name,
            wait_until=wait_until,
            **kwargs)

        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        waiters.wait_for_server_termination,
                        self.servers_client, body['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server, body['id'])
        return body

    def create_group(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(
                self.__class__.__name__ + '-Group')

        group = self.groups_client.create_group(**kwargs)['group']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.delete_group, group['id'])
        waiters.wait_for_volume_resource_status(
            self.groups_client, group['id'], 'available')
        return group

    def delete_group(self, group_id, delete_volumes=True):
        self.groups_client.delete_group(group_id, delete_volumes)
        if delete_volumes:
            vols = self.volumes_client.list_volumes(detail=True)['volumes']
            for vol in vols:
                if vol['group_id'] == group_id:
                    self.volumes_client.wait_for_resource_deletion(vol['id'])
        self.groups_client.wait_for_resource_deletion(group_id)


class BaseVolumeAdminTest(BaseVolumeTest):
    """Base test case class for all Volume Admin API tests."""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseVolumeAdminTest, cls).setup_clients()

        cls.admin_volume_qos_client = cls.os_admin.volume_qos_v2_client
        cls.admin_volume_services_client = \
            cls.os_admin.volume_services_v2_client
        cls.admin_volume_types_client = cls.os_admin.volume_types_v2_client
        cls.admin_volume_manage_client = cls.os_admin.volume_manage_v2_client
        cls.admin_volume_client = cls.os_admin.volumes_v2_client
        if cls._api_version == 3:
            cls.admin_volume_client = cls.os_admin.volumes_v3_client
            cls.admin_groups_client = cls.os_admin.groups_v3_client
            cls.admin_messages_client = cls.os_admin.volume_v3_messages_client
            cls.admin_group_snapshots_client = \
                cls.os_admin.group_snapshots_v3_client
            cls.admin_group_types_client = cls.os_admin.group_types_v3_client
        cls.admin_hosts_client = cls.os_admin.volume_hosts_v2_client
        cls.admin_snapshot_manage_client = \
            cls.os_admin.snapshot_manage_v2_client
        cls.admin_snapshots_client = cls.os_admin.snapshots_v2_client
        cls.admin_backups_client = cls.os_admin.backups_v2_client
        cls.admin_encryption_types_client = \
            cls.os_admin.encryption_types_v2_client
        cls.admin_quota_classes_client = \
            cls.os_admin.volume_quota_classes_v2_client
        cls.admin_quotas_client = cls.os_admin.volume_quotas_v2_client
        cls.admin_volume_limits_client = cls.os_admin.volume_v2_limits_client
        cls.admin_capabilities_client = \
            cls.os_admin.volume_capabilities_v2_client
        cls.admin_scheduler_stats_client = \
            cls.os_admin.volume_scheduler_stats_v2_client

    @classmethod
    def create_test_qos_specs(cls, name=None, consumer=None, **kwargs):
        """create a test Qos-Specs."""
        name = name or data_utils.rand_name(cls.__name__ + '-QoS')
        consumer = consumer or 'front-end'
        qos_specs = cls.admin_volume_qos_client.create_qos(
            name=name, consumer=consumer, **kwargs)['qos_specs']
        cls.addClassResourceCleanup(cls.clear_qos_spec, qos_specs['id'])
        return qos_specs

    @classmethod
    def create_volume_type(cls, name=None, **kwargs):
        """Create a test volume-type"""
        name = name or data_utils.rand_name(cls.__name__ + '-volume-type')
        volume_type = cls.admin_volume_types_client.create_volume_type(
            name=name, **kwargs)['volume_type']
        cls.addClassResourceCleanup(cls.clear_volume_type, volume_type['id'])
        return volume_type

    def create_group_type(self, name=None, **kwargs):
        """Create a test group-type"""
        name = name or data_utils.rand_name(
            self.__class__.__name__ + '-group-type')
        group_type = self.admin_group_types_client.create_group_type(
            name=name, **kwargs)['group_type']
        self.addCleanup(self.admin_group_types_client.delete_group_type,
                        group_type['id'])
        return group_type

    @classmethod
    def clear_qos_spec(cls, qos_id):
        test_utils.call_and_ignore_notfound_exc(
            cls.admin_volume_qos_client.delete_qos, qos_id)

        test_utils.call_and_ignore_notfound_exc(
            cls.admin_volume_qos_client.wait_for_resource_deletion, qos_id)

    @classmethod
    def clear_volume_type(cls, vol_type_id):
        test_utils.call_and_ignore_notfound_exc(
            cls.admin_volume_types_client.delete_volume_type, vol_type_id)

        test_utils.call_and_ignore_notfound_exc(
            cls.admin_volume_types_client.wait_for_resource_deletion,
            vol_type_id)
