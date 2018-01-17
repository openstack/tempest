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
    """

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(TestVolumeMigrateRetypeAttached, cls).setup_clients()
        cls.admin_volumes_client = cls.os_admin.volumes_v2_client

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
        return source_body['name'], dest_body['name']

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
    def test_volume_migrate_attached(self):
        LOG.info("Creating keypair and security group")
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # create volume types
        LOG.info("Creating Volume types")
        source_type, dest_type = self._create_volume_types()

        # create an instance from volume
        LOG.info("Booting instance from volume")
        volume_origin = self.create_volume(imageRef=CONF.compute.image_ref,
                                           volume_type=source_type)

        instance = self._boot_instance_from_volume(volume_origin['id'],
                                                   keypair, security_group)

        # write content to volume on instance
        LOG.info("Setting timestamp in instance %s", instance['id'])
        ip_instance = self.get_server_ip(instance)
        timestamp = self.create_timestamp(ip_instance,
                                          private_key=keypair['private_key'])

        # retype volume with migration from backend #1 to backend #2
        LOG.info("Retyping Volume %s to new type %s", volume_origin['id'],
                 dest_type)
        self._volume_retype_with_migration(volume_origin['id'], dest_type)

        # check the content of written file
        LOG.info("Getting timestamp in postmigrated instance %s",
                 instance['id'])
        timestamp2 = self.get_timestamp(ip_instance,
                                        private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)
