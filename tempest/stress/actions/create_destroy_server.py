# Copyright 2013 Quanta Research Cambridge, Inc.
#
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


def create_destroy(manager, logger):
    image = manager.config.compute.image_ref
    flavor = manager.config.compute.flavor_ref
    while True:
        name = rand_name("instance")
        logger.info("creating %s" % name)
        resp, server = manager.servers_client.create_server(
            name, image, flavor)
        server_id = server['id']
        assert(resp.status == 202)
        manager.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        logger.info("created %s" % server_id)
        logger.info("deleting %s" % name)
        resp, _ = manager.servers_client.delete_server(server_id)
        assert(resp.status == 204)
        manager.servers_client.wait_for_server_termination(server_id)
        logger.info("deleted %s" % server_id)
