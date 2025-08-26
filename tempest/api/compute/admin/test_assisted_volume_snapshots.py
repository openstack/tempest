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

from tempest.api.compute import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


CONF = config.CONF


class VolumesAssistedSnapshotsTest(base.BaseV2ComputeAdminTest):
    """Test volume assisted snapshots"""

    create_default_network = True

    credentials = ['primary', 'admin', ['service_user', 'admin', 'service']]

    @classmethod
    def skip_checks(cls):
        super(VolumesAssistedSnapshotsTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
            # NOTE(gmaan): If new policy is enforced and and service role
            # is present in nova then use service user (no admin role) for
            # assisted volume snapshots APIs.
            if (CONF.enforce_scope.nova and 'service' in
                CONF.compute_feature_enabled.nova_policy_roles):
                cls.credentials = [
                    'primary', 'admin', ['service_user', 'service']]

    @classmethod
    def setup_clients(cls):
        super(VolumesAssistedSnapshotsTest, cls).setup_clients()
        cls.assisted_v_client = (
            cls.os_service_user.assisted_volume_snapshots_client)
        cls.volumes_client = cls.os_admin.volumes_client_latest
        cls.servers_client = cls.os_admin.servers_client

    @decorators.idempotent_id('8aee84a3-1b1f-42e4-9b00-613931ccac24')
    def test_volume_assisted_snapshot_create_delete(self):
        """Test create/delete volume assisted snapshot"""
        volume = self.create_volume()
        self.addCleanup(self.delete_volume, volume['id'])
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        server = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='SSHABLE'
        )
        # Attach created volume to server
        self.attach_volume(server, volume)
        snapshot_id = data_utils.rand_uuid()
        snapshot = self.assisted_v_client.create_assisted_volume_snapshot(
            volume_id=volume['id'], snapshot_id=snapshot_id,
            type='qcow2', new_file='new_file')['snapshot']
        self.assisted_v_client.delete_assisted_volume_snapshot(
            volume_id=volume['id'], snapshot_id=snapshot['id'])
