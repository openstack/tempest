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

from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseVolumeTest(tempest.test.BaseTestCase):
    """Base test case class for all Cinder API tests."""

    _api_version = 2
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(BaseVolumeTest, cls).setUpClass()

        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        cls.os = cls.get_client_manager()

        cls.servers_client = cls.os.servers_client
        cls.image_ref = CONF.compute.image_ref
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.build_interval = CONF.volume.build_interval
        cls.build_timeout = CONF.volume.build_timeout
        cls.snapshots = []
        cls.volumes = []

        if cls._api_version == 1:
            if not CONF.volume_feature_enabled.api_v1:
                msg = "Volume API v1 is disabled"
                raise cls.skipException(msg)
            cls.snapshots_client = cls.os.snapshots_client
            cls.volumes_client = cls.os.volumes_client
            cls.backups_client = cls.os.backups_client
            cls.volume_services_client = cls.os.volume_services_client
            cls.volumes_extension_client = cls.os.volumes_extension_client
            cls.availability_zone_client = (
                cls.os.volume_availability_zone_client)
            # Special fields and resp code for cinder v1
            cls.special_fields = {'name_field': 'display_name',
                                  'descrip_field': 'display_description'}

        elif cls._api_version == 2:
            if not CONF.volume_feature_enabled.api_v2:
                msg = "Volume API v2 is disabled"
                raise cls.skipException(msg)
            cls.volumes_client = cls.os.volumes_v2_client
            cls.volumes_extension_client = cls.os.volumes_v2_extension_client
            cls.availability_zone_client = (
                cls.os.volume_v2_availability_zone_client)
            # Special fields and resp code for cinder v2
            cls.special_fields = {'name_field': 'name',
                                  'descrip_field': 'description'}

        else:
            msg = ("Invalid Cinder API version (%s)" % cls._api_version)
            raise exceptions.InvalidConfiguration(message=msg)

    @classmethod
    def tearDownClass(cls):
        cls.clear_snapshots()
        cls.clear_volumes()
        cls.clear_isolated_creds()
        super(BaseVolumeTest, cls).tearDownClass()

    @classmethod
    def create_volume(cls, size=1, **kwargs):
        """Wrapper utility that returns a test volume."""
        name = data_utils.rand_name('Volume')

        name_field = cls.special_fields['name_field']

        kwargs[name_field] = name
        _, volume = cls.volumes_client.create_volume(size, **kwargs)

        cls.volumes.append(volume)
        cls.volumes_client.wait_for_volume_status(volume['id'], 'available')
        return volume

    @classmethod
    def create_snapshot(cls, volume_id=1, **kwargs):
        """Wrapper utility that returns a test snapshot."""
        _, snapshot = cls.snapshots_client.create_snapshot(volume_id,
                                                           **kwargs)
        cls.snapshots.append(snapshot)
        cls.snapshots_client.wait_for_snapshot_status(snapshot['id'],
                                                      'available')
        return snapshot

    # NOTE(afazekas): these create_* and clean_* could be defined
    # only in a single location in the source, and could be more general.

    @classmethod
    def clear_volumes(cls):
        for volume in cls.volumes:
            try:
                cls.volumes_client.delete_volume(volume['id'])
            except Exception:
                pass

        for volume in cls.volumes:
            try:
                cls.volumes_client.wait_for_resource_deletion(volume['id'])
            except Exception:
                pass

    @classmethod
    def clear_snapshots(cls):
        for snapshot in cls.snapshots:
            try:
                cls.snapshots_client.delete_snapshot(snapshot['id'])
            except Exception:
                pass

        for snapshot in cls.snapshots:
            try:
                cls.snapshots_client.wait_for_resource_deletion(snapshot['id'])
            except Exception:
                pass


class BaseVolumeV1Test(BaseVolumeTest):
    _api_version = 1


class BaseVolumeV1AdminTest(BaseVolumeV1Test):
    """Base test case class for all Volume Admin API tests."""
    @classmethod
    def setUpClass(cls):
        super(BaseVolumeV1AdminTest, cls).setUpClass()
        cls.adm_user = CONF.identity.admin_username
        cls.adm_pass = CONF.identity.admin_password
        cls.adm_tenant = CONF.identity.admin_tenant_name
        if not all((cls.adm_user, cls.adm_pass, cls.adm_tenant)):
            msg = ("Missing Volume Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        if CONF.compute.allow_tenant_isolation:
            cls.os_adm = clients.Manager(cls.isolated_creds.get_admin_creds(),
                                         interface=cls._interface)
        else:
            cls.os_adm = clients.AdminManager(interface=cls._interface)
        cls.client = cls.os_adm.volume_types_client
        cls.hosts_client = cls.os_adm.volume_hosts_client
        cls.quotas_client = cls.os_adm.volume_quotas_client
