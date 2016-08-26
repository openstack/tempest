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

from tempest.common.utils import data_utils
from tempest import config
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class VolumeCreateDeleteTest(stressaction.StressAction):

    def run(self):
        name = data_utils.rand_name("volume")
        self.logger.info("creating %s" % name)
        volumes_client = self.manager.volumes_client
        volume = volumes_client.create_volume(
            display_name=name, size=CONF.volume.volume_size)['volume']
        vol_id = volume['id']
        volumes_client.wait_for_volume_status(vol_id, 'available')
        self.logger.info("created %s" % volume['id'])
        self.logger.info("deleting %s" % name)
        volumes_client.delete_volume(vol_id)
        volumes_client.wait_for_resource_deletion(vol_id)
        self.logger.info("deleted %s" % vol_id)
