# Copyright(c)2015 NTT corp. All Rights Reserved.
#
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

from tempest.api.object_storage import test_container_sync
from tempest import config
from tempest import test

CONF = config.CONF


# This test can be quite long to run due to its
# dependency on container-sync process running interval.
# You can obviously reduce the container-sync interval in the
# container-server configuration.


class ContainerSyncMiddlewareTest(test_container_sync.ContainerSyncTest):

    @classmethod
    def resource_setup(cls):
        super(ContainerSyncMiddlewareTest, cls).resource_setup()

        # Set container-sync-realms.conf info
        cls.realm_name = CONF.object_storage.realm_name
        cls.key = 'sync_key'
        cls.cluster_name = CONF.object_storage.cluster_name

    @test.attr(type='slow')
    @test.idempotent_id('ea4645a1-d147-4976-82f7-e5a7a3065f80')
    @test.requires_ext(extension='container_sync', service='object')
    def test_container_synchronization(self):
        def make_headers(cont, cont_client):
            # tell first container to synchronize to a second
            account_name = cont_client.base_url.split('/')[-1]

            headers = {'X-Container-Sync-Key': "%s" % (self.key),
                       'X-Container-Sync-To': "//%s/%s/%s/%s" %
                       (self.realm_name, self.cluster_name,
                        str(account_name), str(cont))}
            return headers
        self._test_container_synchronization(make_headers)
