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

from tempest.common.utils.data_utils import rand_name


def create_delete(manager, logger):
    while True:
        name = rand_name("volume")
        logger.info("creating %s" % name)
        resp, volume = manager.volumes_client.create_volume(size=1,
                                                            display_name=name)
        assert(resp.status == 200)
        manager.volumes_client.wait_for_volume_status(volume['id'],
                                                      'available')
        logger.info("created %s" % volume['id'])
        logger.info("deleting %s" % name)
        resp, _ = manager.volumes_client.delete_volume(volume['id'])
        assert(resp.status == 202)
        manager.volumes_client.wait_for_resource_deletion(volume['id'])
        logger.info("deleted %s" % volume['id'])
