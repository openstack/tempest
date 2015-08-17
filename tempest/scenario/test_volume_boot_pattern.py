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

from oslo_log import log

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = log.getLogger(__name__)


class TestVolumeBootPattern(manager.ScenarioTest):

    """
    This test case attempts to reproduce the following steps:

     * Create in Cinder some bootable volume importing a Glance image
     * Boot an instance from the bootable volume
     * Write content to the volume
     * Delete an instance and Boot a new instance from the volume
     * Check written content in the instance
     * Create a volume snapshot while the instance is running
     * Boot an additional instance from the new snapshot based volume
     * Check written content in the instance booted from snapshot
    """
    @classmethod
    def skip_checks(cls):
        super(TestVolumeBootPattern, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    def _create_volume_from_image(self):
        img_uuid = CONF.compute.image_ref
        vol_name = data_utils.rand_name('volume-origin')
        return self.create_volume(name=vol_name, imageRef=img_uuid)

    def _get_bdm(self, vol_id, delete_on_termination=False):
        # NOTE(gfidente): the syntax for block_device_mapping is
        # dev_name=id:type:size:delete_on_terminate
        # where type needs to be "snap" if the server is booted
        # from a snapshot, size instead can be safely left empty
        bd_map = [{
            'device_name': 'vda',
            'volume_id': vol_id,
            'delete_on_termination': str(int(delete_on_termination))}]
        return {'block_device_mapping': bd_map}

    def _boot_instance_from_volume(self, vol_id, keypair=None,
                                   security_group=None,
                                   delete_on_termination=False):
        create_kwargs = dict()
        if keypair:
            create_kwargs['key_name'] = keypair['name']
        if security_group:
            create_kwargs['security_groups'] = [
                {'name': security_group['name']}]
        create_kwargs.update(self._get_bdm(
            vol_id, delete_on_termination=delete_on_termination))
        return self.create_server(image='', create_kwargs=create_kwargs)

    def _create_snapshot_from_volume(self, vol_id):
        snap_name = data_utils.rand_name('snapshot')
        snap = self.snapshots_client.create_snapshot(
            volume_id=vol_id,
            force=True,
            display_name=snap_name)
        self.addCleanup(
            self.snapshots_client.wait_for_resource_deletion, snap['id'])
        self.addCleanup(self.snapshots_client.delete_snapshot, snap['id'])
        self.snapshots_client.wait_for_snapshot_status(snap['id'], 'available')
        self.assertEqual(snap_name, snap['display_name'])
        return snap

    def _create_volume_from_snapshot(self, snap_id):
        vol_name = data_utils.rand_name('volume')
        return self.create_volume(name=vol_name, snapshot_id=snap_id)

    def _stop_instances(self, instances):
        # NOTE(gfidente): two loops so we do not wait for the status twice
        for i in instances:
            self.servers_client.stop(i['id'])
        for i in instances:
            waiters.wait_for_server_status(self.servers_client,
                                           i['id'], 'SHUTOFF')

    def _detach_volumes(self, volumes):
        # NOTE(gfidente): two loops so we do not wait for the status twice
        for v in volumes:
            self.volumes_client.detach_volume(v['id'])
        for v in volumes:
            self.volumes_client.wait_for_volume_status(v['id'], 'available')

    def _ssh_to_server(self, server, keypair):
        if CONF.compute.use_floatingip_for_ssh:
            floating_ip = self.floating_ips_client.create_floating_ip()
            self.addCleanup(self.delete_wrapper,
                            self.floating_ips_client.delete_floating_ip,
                            floating_ip['id'])
            self.floating_ips_client.associate_floating_ip_to_server(
                floating_ip['ip'], server['id'])
            ip = floating_ip['ip']
        else:
            ip = server

        return self.get_remote_client(ip, private_key=keypair['private_key'],
                                      log_console_of_servers=[server])

    def _get_content(self, ssh_client):
        return ssh_client.exec_command('cat /tmp/text')

    def _write_text(self, ssh_client):
        text = data_utils.rand_name('text')
        ssh_client.exec_command('echo "%s" > /tmp/text; sync' % (text))

        return self._get_content(ssh_client)

    def _delete_server(self, server):
        self.servers_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])

    def _check_content_of_written_file(self, ssh_client, expected):
        actual = self._get_content(ssh_client)
        self.assertEqual(expected, actual)

    @test.idempotent_id('557cd2c2-4eb8-4dce-98be-f86765ff311b')
    @test.attr(type='smoke')
    @test.services('compute', 'volume', 'image')
    def test_volume_boot_pattern(self):
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # create an instance from volume
        volume_origin = self._create_volume_from_image()
        instance_1st = self._boot_instance_from_volume(volume_origin['id'],
                                                       keypair, security_group)

        # write content to volume on instance
        ssh_client_for_instance_1st = self._ssh_to_server(instance_1st,
                                                          keypair)
        text = self._write_text(ssh_client_for_instance_1st)

        # delete instance
        self._delete_server(instance_1st)

        # create a 2nd instance from volume
        instance_2nd = self._boot_instance_from_volume(volume_origin['id'],
                                                       keypair, security_group)

        # check the content of written file
        ssh_client_for_instance_2nd = self._ssh_to_server(instance_2nd,
                                                          keypair)
        self._check_content_of_written_file(ssh_client_for_instance_2nd, text)

        # snapshot a volume
        snapshot = self._create_snapshot_from_volume(volume_origin['id'])

        # create a 3rd instance from snapshot
        volume = self._create_volume_from_snapshot(snapshot['id'])
        instance_from_snapshot = (
            self._boot_instance_from_volume(volume['id'],
                                            keypair, security_group))

        # check the content of written file
        ssh_client = self._ssh_to_server(instance_from_snapshot, keypair)
        self._check_content_of_written_file(ssh_client, text)

        # NOTE(gfidente): ensure resources are in clean state for
        # deletion operations to succeed
        self._stop_instances([instance_2nd, instance_from_snapshot])

    @test.idempotent_id('36c34c67-7b54-4b59-b188-02a2f458a63b')
    @test.services('compute', 'volume', 'image')
    def test_create_ebs_image_and_check_boot(self):
        # create an instance from volume
        volume_origin = self._create_volume_from_image()
        instance = self._boot_instance_from_volume(volume_origin['id'],
                                                   delete_on_termination=True)
        # create EBS image
        name = data_utils.rand_name('image')
        image = self.create_server_snapshot(instance, name=name)

        # delete instance
        self._delete_server(instance)

        # boot instance from EBS image
        instance = self.create_server(image=image['id'])
        # just ensure that instance booted

        # delete instance
        self._delete_server(instance)


class TestVolumeBootPatternV2(TestVolumeBootPattern):
    def _get_bdm(self, vol_id, delete_on_termination=False):
        bd_map_v2 = [{
            'uuid': vol_id,
            'source_type': 'volume',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': delete_on_termination}]
        return {'block_device_mapping_v2': bd_map_v2}
