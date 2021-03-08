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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestVolumeMigrateRetypeAttached(manager.ScenarioTest):

    """This test case attempts to reproduce the following steps:

     * Create 2 volume types representing 2 different backends
     * Create in Cinder some bootable volume importing a Glance image using
     *   volume_type_1
     * Boot an instance from the bootable volume
     * Write to the volume
     * Perform a cinder retype --on-demand of the volume to type of backend #2
     * Check written content of migrated volume
     * Check the type of the volume has been updated.
     * Check the volume is still in-use and the migration was successful.
     * Check that the same volume is attached to the instance.
    """

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(TestVolumeMigrateRetypeAttached, cls).setup_clients()
        cls.admin_volumes_client = cls.os_admin.volumes_client_latest

    @classmethod
    def skip_checks(cls):
        super(TestVolumeMigrateRetypeAttached, cls).skip_checks()
        if not CONF.volume_feature_enabled.multi_backend:
            raise cls.skipException("Cinder multi-backend feature disabled")

        if len(set(CONF.volume.backend_names)) < 2:
            raise cls.skipException("Requires at least two different "
                                    "backend names")

    def _boot_instance_from_volume(self, vol_id, keypair, security_group):

        key_name = keypair['name']
        security_groups = [{'name': security_group['name']}]
        block_device_mapping = [{'device_name': 'vda', 'volume_id': vol_id,
                                 'delete_on_termination': False}]

        return self.create_server(image_id='',
                                  key_name=key_name,
                                  security_groups=security_groups,
                                  block_device_mapping=block_device_mapping)

    def _create_volume_types(self):
        backend_names = CONF.volume.backend_names

        backend_source = backend_names[0]
        backend_dest = backend_names[1]

        source_body = self.create_volume_type(backend_name=backend_source)
        dest_body = self.create_volume_type(backend_name=backend_dest)

        LOG.info("Created Volume types: %(src)s -> %(src_backend)s, %(dst)s "
                 "-> %(dst_backend)s", {'src': source_body['name'],
                                        'src_backend': backend_source,
                                        'dst': dest_body['name'],
                                        'dst_backend': backend_dest})
        return ({'name': source_body['name'], 'host': backend_source},
                {'name': dest_body['name'], 'host': backend_dest})

    def _volume_retype_with_migration(self, volume_id, new_volume_type):
        # NOTE: The 'on-demand' migration requires admin operation, so
        # admin_volumes_client() should be used here.
        migration_policy = 'on-demand'
        self.admin_volumes_client.retype_volume(
            volume_id, new_type=new_volume_type,
            migration_policy=migration_policy)
        waiters.wait_for_volume_retype(self.volumes_client,
                                       volume_id, new_volume_type)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('deadd2c2-beef-4dce-98be-f86765ff311b')
    @utils.services('compute', 'volume')
    def test_volume_retype_attached(self):
        LOG.info("Creating keypair and security group")
        keypair = self.create_keypair()
        security_group = self.create_security_group()

        # create volume types
        LOG.info("Creating Volume types")
        source_type, dest_type = self._create_volume_types()

        # create an instance from volume
        LOG.info("Booting instance from volume")
        volume_id = self.create_volume(imageRef=CONF.compute.image_ref,
                                       volume_type=source_type['name'])['id']

        instance = self._boot_instance_from_volume(volume_id, keypair,
                                                   security_group)

        # write content to volume on instance
        LOG.info("Setting timestamp in instance %s", instance['id'])
        ip_instance = self.get_server_ip(instance)
        timestamp = self.create_timestamp(ip_instance,
                                          private_key=keypair['private_key'],
                                          server=instance)

        # retype volume with migration from backend #1 to backend #2
        LOG.info("Retyping Volume %s to new type %s", volume_id,
                 dest_type['name'])
        # This method calls for the retype of the volume before calling a
        # waiter that asserts that the volume type has changed successfully.
        self._volume_retype_with_migration(volume_id, dest_type['name'])

        # check the content of written file
        LOG.info("Getting timestamp in postmigrated instance %s",
                 instance['id'])
        timestamp2 = self.get_timestamp(ip_instance,
                                        private_key=keypair['private_key'],
                                        server=instance)
        self.assertEqual(timestamp, timestamp2)

        # Assert that the volume is on the new host, is still in-use and has a
        # migration_status of success
        volume = self.admin_volumes_client.show_volume(volume_id)['volume']
        # dest_type is host@backend, os-vol-host-attr:host is host@backend#type
        self.assertIn(dest_type['host'], volume['os-vol-host-attr:host'])
        self.assertEqual('in-use', volume['status'])
        self.assertEqual('success', volume['migration_status'])

        # Assert that the same volume id is attached to the instance, ensuring
        # the os-migrate_volume_completion Cinder API has been called.
        attached_volumes = self.servers_client.list_volume_attachments(
            instance['id'])['volumeAttachments']
        self.assertEqual(volume_id, attached_volumes[0]['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('fe47b1ed-640e-4e3b-a090-200e25607362')
    @utils.services('compute', 'volume')
    def test_volume_migrate_attached(self):
        LOG.info("Creating keypair and security group")
        keypair = self.create_keypair()
        security_group = self.create_security_group()

        LOG.info("Creating volume")
        # Create a unique volume type to avoid using the backend default
        migratable_type = self.create_volume_type()['name']
        volume_id = self.create_volume(imageRef=CONF.compute.image_ref,
                                       volume_type=migratable_type)['id']
        volume = self.admin_volumes_client.show_volume(volume_id)

        LOG.info("Booting instance from volume")
        instance = self._boot_instance_from_volume(volume_id, keypair,
                                                   security_group)

        # Identify the source and destination hosts for the migration
        src_host = volume['volume']['os-vol-host-attr:host']

        # Select the first c-vol host that isn't hosting the volume as the dest
        # host['host_name'] should take the format of host@backend.
        # src_host should take the format of host@backend#type
        hosts = self.admin_volumes_client.list_hosts()['hosts']
        for host in hosts:
            if (host['service'] == 'cinder-volume' and
                not src_host.startswith(host['host_name'])):
                dest_host = host['host_name']
                break

        ip_instance = self.get_server_ip(instance)
        timestamp = self.create_timestamp(ip_instance,
                                          private_key=keypair['private_key'],
                                          server=instance)

        LOG.info("Migrating Volume %s from host %s to host %s",
                 volume_id, src_host, dest_host)
        self.admin_volumes_client.migrate_volume(volume_id, host=dest_host)

        # This waiter asserts that the migration_status is success and that
        # the volume has moved to the dest_host
        waiters.wait_for_volume_migration(self.admin_volumes_client, volume_id,
                                          dest_host)

        # check the content of written file
        LOG.info("Getting timestamp in postmigrated instance %s",
                 instance['id'])
        timestamp2 = self.get_timestamp(ip_instance,
                                        private_key=keypair['private_key'],
                                        server=instance)
        self.assertEqual(timestamp, timestamp2)

        # Assert that the volume is in-use
        volume = self.admin_volumes_client.show_volume(volume_id)['volume']
        self.assertEqual('in-use', volume['status'])

        # Assert that the same volume id is attached to the instance, ensuring
        # the os-migrate_volume_completion Cinder API has been called
        attached_volumes = self.servers_client.list_volume_attachments(
            instance['id'])['volumeAttachments']
        attached_volume_id = attached_volumes[0]['id']
        self.assertEqual(volume_id, attached_volume_id)
