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

from oslo_log import log as logging
import testtools

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestVolumeBootPattern(manager.EncryptionScenarioTest):

    # Boot from volume scenario is quite slow, and needs extra
    # breathing room to get through deletes in the time allotted.
    TIMEOUT_SCALING_FACTOR = 2

    @classmethod
    def skip_checks(cls):
        super(TestVolumeBootPattern, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    def _create_volume_from_image(self):
        img_uuid = CONF.compute.image_ref
        vol_name = data_utils.rand_name(
            self.__class__.__name__ + '-volume-origin')
        return self.create_volume(name=vol_name, imageRef=img_uuid)

    def _get_bdm(self, source_id, source_type, delete_on_termination=False):
        bd_map_v2 = [{
            'uuid': source_id,
            'source_type': source_type,
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': delete_on_termination}]
        return {'block_device_mapping_v2': bd_map_v2}

    def _boot_instance_from_resource(self, source_id,
                                     source_type,
                                     keypair=None,
                                     security_group=None,
                                     delete_on_termination=False):
        create_kwargs = dict()
        if keypair:
            create_kwargs['key_name'] = keypair['name']
        if security_group:
            create_kwargs['security_groups'] = [
                {'name': security_group['name']}]
        create_kwargs.update(self._get_bdm(
            source_id,
            source_type,
            delete_on_termination=delete_on_termination))

        return self.create_server(image_id='', **create_kwargs)

    def _delete_server(self, server):
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])

    @decorators.idempotent_id('557cd2c2-4eb8-4dce-98be-f86765ff311b')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @utils.services('compute', 'volume', 'image')
    def test_volume_boot_pattern(self):

        """This test case attempts to reproduce the following steps:

        * Create in Cinder some bootable volume importing a Glance image
        * Boot an instance from the bootable volume
        * Write content to the volume
        * Delete an instance and Boot a new instance from the volume
        * Check written content in the instance
        * Create a volume snapshot while the instance is running
        * Boot an additional instance from the new snapshot based volume
        * Check written content in the instance booted from snapshot
        """

        LOG.info("Creating keypair and security group")
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # create an instance from volume
        LOG.info("Booting instance 1 from volume")
        volume_origin = self._create_volume_from_image()
        instance_1st = self._boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            keypair=keypair,
            security_group=security_group)
        LOG.info("Booted first instance: %s", instance_1st)

        # write content to volume on instance
        LOG.info("Setting timestamp in instance %s", instance_1st)
        ip_instance_1st = self.get_server_ip(instance_1st)
        timestamp = self.create_timestamp(ip_instance_1st,
                                          private_key=keypair['private_key'])

        # delete instance
        LOG.info("Deleting first instance: %s", instance_1st)
        self._delete_server(instance_1st)

        # create a 2nd instance from volume
        instance_2nd = self._boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            keypair=keypair,
            security_group=security_group)
        LOG.info("Booted second instance %s", instance_2nd)

        # check the content of written file
        LOG.info("Getting timestamp in instance %s", instance_2nd)
        ip_instance_2nd = self.get_server_ip(instance_2nd)
        timestamp2 = self.get_timestamp(ip_instance_2nd,
                                        private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)

        # snapshot a volume
        LOG.info("Creating snapshot from volume: %s", volume_origin['id'])
        snapshot = self.create_volume_snapshot(volume_origin['id'], force=True)

        # create a 3rd instance from snapshot
        LOG.info("Creating third instance from snapshot: %s", snapshot['id'])
        volume = self.create_volume(snapshot_id=snapshot['id'],
                                    size=snapshot['size'])
        LOG.info("Booting third instance from snapshot")
        server_from_snapshot = (
            self._boot_instance_from_resource(source_id=volume['id'],
                                              source_type='volume',
                                              keypair=keypair,
                                              security_group=security_group))
        LOG.info("Booted third instance %s", server_from_snapshot)

        # check the content of written file
        LOG.info("Logging into third instance to get timestamp: %s",
                 server_from_snapshot)
        server_from_snapshot_ip = self.get_server_ip(server_from_snapshot)
        timestamp3 = self.get_timestamp(server_from_snapshot_ip,
                                        private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp3)

    @decorators.idempotent_id('05795fb2-b2a7-4c9f-8fac-ff25aedb1489')
    @decorators.attr(type='slow')
    @utils.services('compute', 'image', 'volume')
    def test_create_server_from_volume_snapshot(self):
        # Create a volume from an image
        boot_volume = self._create_volume_from_image()

        # Create a snapshot
        boot_snapshot = self.create_volume_snapshot(boot_volume['id'])

        # Create a server from a volume snapshot
        server = self._boot_instance_from_resource(
            source_id=boot_snapshot['id'],
            source_type='snapshot',
            delete_on_termination=True)

        server_info = self.servers_client.show_server(server['id'])['server']

        # The created volume when creating a server from a snapshot
        created_volume = server_info['os-extended-volumes:volumes_attached']

        self.assertNotEmpty(created_volume, "No volume attachment found.")

        created_volume_info = self.volumes_client.show_volume(
            created_volume[0]['id'])['volume']

        # Verify the server was created from the snapshot
        self.assertEqual(
            boot_volume['volume_image_metadata']['image_id'],
            created_volume_info['volume_image_metadata']['image_id'])
        self.assertEqual(boot_snapshot['id'],
                         created_volume_info['snapshot_id'])
        self.assertEqual(server['id'],
                         created_volume_info['attachments'][0]['server_id'])
        self.assertEqual(created_volume[0]['id'],
                         created_volume_info['attachments'][0]['volume_id'])

    @decorators.idempotent_id('36c34c67-7b54-4b59-b188-02a2f458a63b')
    @utils.services('compute', 'volume', 'image')
    def test_create_ebs_image_and_check_boot(self):
        # create an instance from volume
        volume_origin = self._create_volume_from_image()
        instance = self._boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            delete_on_termination=True)
        # create EBS image
        image = self.create_server_snapshot(instance)

        # delete instance
        self._delete_server(instance)

        # boot instance from EBS image
        instance = self.create_server(image_id=image['id'])
        # just ensure that instance booted

        # delete instance
        self._delete_server(instance)

    @decorators.idempotent_id('cb78919a-e553-4bab-b73b-10cf4d2eb125')
    @testtools.skipUnless(CONF.compute_feature_enabled.attach_encrypted_volume,
                          'Encrypted volume attach is not supported')
    @utils.services('compute', 'volume')
    def test_boot_server_from_encrypted_volume_luks(self):
        # Create an encrypted volume
        volume = self.create_encrypted_volume('nova.volume.encryptors.'
                                              'luks.LuksEncryptor',
                                              volume_type='luks')

        self.volumes_client.set_bootable_volume(volume['id'], bootable=True)

        # Boot a server from the encrypted volume
        server = self._boot_instance_from_resource(
            source_id=volume['id'],
            source_type='volume',
            delete_on_termination=False)

        server_info = self.servers_client.show_server(server['id'])['server']
        created_volume = server_info['os-extended-volumes:volumes_attached']
        self.assertEqual(volume['id'], created_volume[0]['id'])
