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

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class ServerCreateDestroyTest(stressaction.StressAction):

    def setUp(self, **kwargs):
        self.image = CONF.compute.image_ref
        self.flavor = CONF.compute.flavor_ref

    def run(self):
        name = data_utils.rand_name(self.__class__.__name__ + "-instance")
        self.logger.info("creating %s" % name)
        server = self.manager.servers_client.create_server(
            name=name, imageRef=self.image, flavorRef=self.flavor)['server']
        server_id = server['id']
        waiters.wait_for_server_status(self.manager.servers_client, server_id,
                                       'ACTIVE')
        self.logger.info("created %s" % server_id)
        self.logger.info("deleting %s" % name)
        self.manager.servers_client.delete_server(server_id)
        waiters.wait_for_server_termination(self.manager.servers_client,
                                            server_id)
        self.logger.info("deleted %s" % server_id)
