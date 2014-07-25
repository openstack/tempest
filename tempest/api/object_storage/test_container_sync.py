# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

import time
import urlparse

from tempest.api.object_storage import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


# This test can be quite long to run due to its
# dependency on container-sync process running interval.
# You can obviously reduce the container-sync interval in the
# container-server configuration.


class ContainerSyncTest(base.BaseObjectTest):
    clients = {}

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ContainerSyncTest, cls).setUpClass()
        cls.containers = []
        cls.objects = []

        # Default container-server config only allows localhost
        cls.local_ip = '127.0.0.1'

        # Must be configure according to container-sync interval
        container_sync_timeout = \
            int(CONF.object_storage.container_sync_timeout)
        cls.container_sync_interval = \
            int(CONF.object_storage.container_sync_interval)
        cls.attempts = \
            int(container_sync_timeout / cls.container_sync_interval)

        # define container and object clients
        cls.clients[data_utils.rand_name(name='TestContainerSync')] = \
            (cls.container_client, cls.object_client)
        cls.clients[data_utils.rand_name(name='TestContainerSync')] = \
            (cls.container_client_alt, cls.object_client_alt)
        for cont_name, client in cls.clients.items():
            client[0].create_container(cont_name)
            cls.containers.append(cont_name)

    @classmethod
    def tearDownClass(cls):
        for client in cls.clients.values():
            cls.delete_containers(cls.containers, client[0], client[1])
        super(ContainerSyncTest, cls).tearDownClass()

    @test.attr(type='slow')
    @test.skip_because(bug='1317133')
    def test_container_synchronization(self):
        # container to container synchronization
        # to allow/accept sync requests to/from other accounts

        # turn container synchronization on and create object in container
        for cont in (self.containers, self.containers[::-1]):
            cont_client = [self.clients[c][0] for c in cont]
            obj_client = [self.clients[c][1] for c in cont]
            # tell first container to synchronize to a second
            client_proxy_ip = \
                urlparse.urlparse(cont_client[1].base_url).netloc.split(':')[0]
            client_base_url = \
                cont_client[1].base_url.replace(client_proxy_ip,
                                                self.local_ip)
            headers = {'X-Container-Sync-Key': 'sync_key',
                       'X-Container-Sync-To': "%s/%s" %
                       (client_base_url, str(cont[1]))}
            resp, body = \
                cont_client[0].put(str(cont[0]), body=None, headers=headers)
            self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
            # create object in container
            object_name = data_utils.rand_name(name='TestSyncObject')
            data = object_name[::-1]  # data_utils.arbitrary_string()
            resp, _ = obj_client[0].create_object(cont[0], object_name, data)
            self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
            self.objects.append(object_name)

        # wait until container contents list is not empty
        cont_client = [self.clients[c][0] for c in self.containers]
        params = {'format': 'json'}
        while self.attempts > 0:
            object_lists = []
            for client_index in (0, 1):
                resp, object_list = \
                    cont_client[client_index].\
                    list_container_contents(self.containers[client_index],
                                            params=params)
                self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
                object_lists.append(dict(
                    (obj['name'], obj) for obj in object_list))
            # check that containers are not empty and have equal keys()
            # or wait for next attempt
            if not object_lists[0] or not object_lists[1] or \
                    set(object_lists[0].keys()) != set(object_lists[1].keys()):
                time.sleep(self.container_sync_interval)
                self.attempts -= 1
            else:
                break

        self.assertEqual(object_lists[0], object_lists[1],
                         'Different object lists in containers.')

        # Verify object content
        obj_clients = [(self.clients[c][1], c) for c in self.containers]
        for obj_client, cont in obj_clients:
            for obj_name in object_lists[0]:
                resp, object_content = obj_client.get_object(cont, obj_name)
                self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
                self.assertEqual(object_content, obj_name[::-1])
