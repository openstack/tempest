# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.common.utils.data_utils import rand_name
from tempest.scenario import manager


class TestVolumeSnapshotPattern(manager.OfficialClientTest):

    """
    This test case attempts to reproduce the following steps:

     * Create in Cinder some bootable volume importing a Glance image
     * Boot an instance from the bootable volume
     * Create a volume snapshot while the instance is running
     * Boot an additional instance from the new snapshot based volume
    """

    def _create_volume_from_image(self):
        img_uuid = self.config.compute.image_ref
        vol_name = rand_name('volume-origin')
        return self.create_volume(name=vol_name, imageRef=img_uuid)

    def _boot_instance_from_volume(self, vol_id):
        # NOTE(gfidente): the syntax for block_device_mapping is
        # dev_name=id:type:size:delete_on_terminate
        # where type needs to be "snap" if the server is booted
        # from a snapshot, size instead can be safely left empty
        bd_map = {
            'vda': vol_id + ':::0'
        }
        create_kwargs = {
            'block_device_mapping': bd_map
        }
        return self.create_server(self.compute_client,
                                  create_kwargs=create_kwargs)

    def _create_snapshot_from_volume(self, vol_id):
        volume_snapshots = self.volume_client.volume_snapshots
        snap_name = rand_name('snapshot')
        snap = volume_snapshots.create(volume_id=vol_id,
                                       force=True,
                                       display_name=snap_name)
        self.set_resource(snap.id, snap)
        self.status_timeout(volume_snapshots,
                            snap.id,
                            'available')
        return snap

    def _create_volume_from_snapshot(self, snap_id):
        vol_name = rand_name('volume')
        return self.create_volume(name=vol_name, snapshot_id=snap_id)

    def _stop_instances(self, instances):
        # NOTE(gfidente): two loops so we do not wait for the status twice
        for i in instances:
            self.compute_client.servers.stop(i)
        for i in instances:
            self.status_timeout(self.compute_client.servers,
                                i.id,
                                'SHUTOFF')

    def _detach_volumes(self, volumes):
        # NOTE(gfidente): two loops so we do not wait for the status twice
        for v in volumes:
            self.volume_client.volumes.detach(v)
        for v in volumes:
            self.status_timeout(self.volume_client.volumes,
                                v.id,
                                'available')

    def test_volume_snapshot_pattern(self):
        volume_origin = self._create_volume_from_image()
        i_origin = self._boot_instance_from_volume(volume_origin.id)
        snapshot = self._create_snapshot_from_volume(volume_origin.id)
        volume = self._create_volume_from_snapshot(snapshot.id)
        i = self._boot_instance_from_volume(volume.id)
        # NOTE(gfidente): ensure resources are in clean state for
        # deletion operations to succeed
        self._stop_instances([i_origin, i])
        self._detach_volumes([volume_origin, volume])
