# (c) 2013 Deutsche Telekom AG
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from tempest_lib.common.utils import data_utils

from tempest import config
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class VolumeAttachDeleteTest(stressaction.StressAction):

    def setUp(self, **kwargs):
        self.image = CONF.compute.image_ref
        self.flavor = CONF.compute.flavor_ref

    def run(self):
        # Step 1: create volume
        name = data_utils.rand_name("volume")
        self.logger.info("creating volume: %s" % name)
        volume = self.manager.volumes_client.create_volume(
            display_name=name)
        self.manager.volumes_client.wait_for_volume_status(volume['id'],
                                                           'available')
        self.logger.info("created volume: %s" % volume['id'])

        # Step 2: create vm instance
        vm_name = data_utils.rand_name("instance")
        self.logger.info("creating vm: %s" % vm_name)
        server = self.manager.servers_client.create_server(
            vm_name, self.image, self.flavor)
        server_id = server['id']
        self.manager.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.logger.info("created vm %s" % server_id)

        # Step 3: attach volume to vm
        self.logger.info("attach volume (%s) to vm %s" %
                         (volume['id'], server_id))
        self.manager.servers_client.attach_volume(server_id,
                                                  volume['id'],
                                                  '/dev/vdc')
        self.manager.volumes_client.wait_for_volume_status(volume['id'],
                                                           'in-use')
        self.logger.info("volume (%s) attached to vm %s" %
                         (volume['id'], server_id))

        # Step 4: delete vm
        self.logger.info("deleting vm: %s" % vm_name)
        self.manager.servers_client.delete_server(server_id)
        self.manager.servers_client.wait_for_server_termination(server_id)
        self.logger.info("deleted vm: %s" % server_id)

        # Step 5: delete volume
        self.logger.info("deleting volume: %s" % volume['id'])
        self.manager.volumes_client.delete_volume(volume['id'])
        self.manager.volumes_client.wait_for_resource_deletion(volume['id'])
        self.logger.info("deleted volume: %s" % volume['id'])
