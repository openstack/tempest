# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.openstack.common import log as logging
import tempest.test

LOG = logging.getLogger(__name__)


class BaseVolumeTest(tempest.test.BaseTestCase):

    """Base test case class for all Cinder API tests."""

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(BaseVolumeTest, cls).setUpClass()

        if not cls.config.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        cls.os = cls.get_client_manager()

        cls.volumes_client = cls.os.volumes_client
        cls.snapshots_client = cls.os.snapshots_client
        cls.servers_client = cls.os.servers_client
        cls.volumes_extension_client = cls.os.volumes_extension_client
        cls.image_ref = cls.config.compute.image_ref
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.build_interval = cls.config.volume.build_interval
        cls.build_timeout = cls.config.volume.build_timeout
        cls.snapshots = []
        cls.volumes = []

    @classmethod
    def tearDownClass(cls):
        cls.clear_snapshots()
        cls.clear_volumes()
        cls.clear_isolated_creds()
        super(BaseVolumeTest, cls).tearDownClass()

    @classmethod
    def create_snapshot(cls, volume_id=1, **kwargs):
        """Wrapper utility that returns a test snapshot."""
        resp, snapshot = cls.snapshots_client.create_snapshot(volume_id,
                                                              **kwargs)
        assert 200 == resp.status
        cls.snapshots.append(snapshot)
        cls.snapshots_client.wait_for_snapshot_status(snapshot['id'],
                                                      'available')
        return snapshot

    # NOTE(afazekas): these create_* and clean_* could be defined
    # only in a single location in the source, and could be more general.

    @classmethod
    def create_volume(cls, size=1, **kwargs):
        """Wrapper utility that returns a test volume."""
        vol_name = data_utils.rand_name('Volume')
        resp, volume = cls.volumes_client.create_volume(size,
                                                        display_name=vol_name,
                                                        **kwargs)
        assert 200 == resp.status
        cls.volumes.append(volume)
        cls.volumes_client.wait_for_volume_status(volume['id'], 'available')
        return volume

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
    @classmethod
    def setUpClass(cls):
        if not cls.config.volume_feature_enabled.api_v1:
            msg = "Volume API v1 not supported"
            raise cls.skipException(msg)
        super(BaseVolumeV1Test, cls).setUpClass()
        cls.volumes_client = cls.os.volumes_client
        cls.volumes_client.keystone_auth(cls.os.username,
                                         cls.os.password,
                                         cls.os.auth_url,
                                         cls.volumes_client.service,
                                         cls.os.tenant_name)


class BaseVolumeV1AdminTest(BaseVolumeV1Test):
    """Base test case class for all Volume Admin API tests."""
    @classmethod
    def setUpClass(cls):
        super(BaseVolumeV1AdminTest, cls).setUpClass()
        cls.adm_user = cls.config.identity.admin_username
        cls.adm_pass = cls.config.identity.admin_password
        cls.adm_tenant = cls.config.identity.admin_tenant_name
        if not all((cls.adm_user, cls.adm_pass, cls.adm_tenant)):
            msg = ("Missing Volume Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = creds
            cls.os_adm = clients.Manager(username=admin_username,
                                         password=admin_password,
                                         tenant_name=admin_tenant_name,
                                         interface=cls._interface)
        else:
            cls.os_adm = clients.AdminManager(interface=cls._interface)
        cls.client = cls.os_adm.volume_types_client
        cls.hosts_client = cls.os_adm.volume_hosts_client
