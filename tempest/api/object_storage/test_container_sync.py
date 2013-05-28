# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import testtools

from tempest.api.object_storage import base
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


class ContainerSyncTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ContainerSyncTest, cls).setUpClass()
        cls.containers = []
        cls.objects = []
        container_sync_timeout = \
            int(cls.config.object_storage.container_sync_timeout)
        cls.container_sync_interval = \
            int(cls.config.object_storage.container_sync_interval)
        cls.attempts = \
            int(container_sync_timeout / cls.container_sync_interval)
        # define container and object clients
        cls.clients = {}
        cls.clients[rand_name(name='TestContainerSync')] = \
            (cls.container_client, cls.object_client)
        cls.clients[rand_name(name='TestContainerSync')] = \
            (cls.container_client_alt, cls.object_client_alt)
        for cont_name, client in cls.clients.items():
            client[0].create_container(cont_name)
            cls.containers.append(cont_name)

    @classmethod
    def tearDownClass(cls):
        for client in cls.clients.values():
            cls.delete_containers(cls.containers, client[0], client[1])

    @testtools.skip('Until Bug #1093743 is resolved.')
    @attr(type='gate')
    def test_container_synchronization(self):
        # container to container synchronization
        # to allow/accept sync requests to/from other accounts

        # turn container synchronization on and create object in container
        for cont in (self.containers, self.containers[::-1]):
            cont_client = [self.clients[c][0] for c in cont]
            obj_client = [self.clients[c][1] for c in cont]
            # tell first container to synchronize to a second
            headers = {'X-Container-Sync-Key': 'sync_key',
                       'X-Container-Sync-To': "%s/%s" %
                       (cont_client[1].base_url, str(cont[1]))}
            resp, body = \
                cont_client[0].put(str(cont[0]), body=None, headers=headers)
            self.assertTrue(resp['status'] in ('202', '201'),
                            'Error installing X-Container-Sync-To '
                            'for the container "%s"' % (cont[0]))
            # create object in container
            object_name = rand_name(name='TestSyncObject')
            data = object_name[::-1]  # arbitrary_string()
            resp, _ = obj_client[0].create_object(cont[0], object_name, data)
            self.assertEqual(resp['status'], '201',
                             'Error creating the object "%s" in'
                             'the container "%s"'
                             % (object_name, cont[0]))
            self.objects.append(object_name)

        # wait until container contents list is not empty
        cont_client = [self.clients[c][0] for c in self.containers]
        params = {'format': 'json'}
        while self.attempts > 0:
            # get first container content
            resp, object_list_0 = \
                cont_client[0].\
                list_container_contents(self.containers[0], params=params)
            self.assertEqual(resp['status'], '200',
                             'Error listing the destination container`s'
                             ' "%s" contents' % (self.containers[0]))
            object_list_0 = dict((obj['name'], obj) for obj in object_list_0)
            # get second container content
            resp, object_list_1 = \
                cont_client[1].\
                list_container_contents(self.containers[1], params=params)
            self.assertEqual(resp['status'], '200',
                             'Error listing the destination container`s'
                             ' "%s" contents' % (self.containers[1]))
            object_list_1 = dict((obj['name'], obj) for obj in object_list_1)
            # check that containers are not empty and have equal keys()
            # or wait for next attempt
            if not object_list_0 or not object_list_1 or \
                    set(object_list_0.keys()) != set(object_list_1.keys()):
                time.sleep(self.container_sync_interval)
                self.attempts -= 1
            else:
                break
        self.assertEqual(object_list_0, object_list_1,
                         'Different object lists in containers.')
