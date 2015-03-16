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

import testtools

from tempest_lib.common.utils import data_utils

from tempest.api.object_storage import base
from tempest import config
from tempest import test

CONF = config.CONF


class ContainerTest(base.BaseObjectTest):
    @classmethod
    def resource_setup(cls):
        super(ContainerTest, cls).resource_setup()
        cls.containers = []

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers(cls.containers)
        super(ContainerTest, cls).resource_cleanup()

    def assertContainer(self, container, count, byte, versioned):
        resp, _ = self.container_client.list_container_metadata(container)
        self.assertHeaders(resp, 'Container', 'HEAD')
        header_value = resp.get('x-container-object-count', 'Missing Header')
        self.assertEqual(header_value, count)
        header_value = resp.get('x-container-bytes-used', 'Missing Header')
        self.assertEqual(header_value, byte)
        header_value = resp.get('x-versions-location', 'Missing Header')
        self.assertEqual(header_value, versioned)

    @test.attr(type='smoke')
    @test.idempotent_id('a151e158-dcbf-4a1f-a1e7-46cd65895a6f')
    @testtools.skipIf(
        not CONF.object_storage_feature_enabled.object_versioning,
        'Object-versioning is disabled')
    def test_versioned_container(self):
        # create container
        vers_container_name = data_utils.rand_name(name='TestVersionContainer')
        resp, body = self.container_client.create_container(
            vers_container_name)
        self.containers.append(vers_container_name)
        self.assertHeaders(resp, 'Container', 'PUT')
        self.assertContainer(vers_container_name, '0', '0', 'Missing Header')

        base_container_name = data_utils.rand_name(name='TestBaseContainer')
        headers = {'X-versions-Location': vers_container_name}
        resp, body = self.container_client.create_container(
            base_container_name,
            metadata=headers,
            metadata_prefix='')
        self.containers.append(base_container_name)
        self.assertHeaders(resp, 'Container', 'PUT')
        self.assertContainer(base_container_name, '0', '0',
                             vers_container_name)
        object_name = data_utils.rand_name(name='TestObject')
        # create object
        resp, _ = self.object_client.create_object(base_container_name,
                                                   object_name, '1')
        # create 2nd version of object
        resp, _ = self.object_client.create_object(base_container_name,
                                                   object_name, '2')
        resp, body = self.object_client.get_object(base_container_name,
                                                   object_name)
        self.assertEqual(body, '2')
        # delete object version 2
        resp, _ = self.object_client.delete_object(base_container_name,
                                                   object_name)
        self.assertContainer(base_container_name, '1', '1',
                             vers_container_name)
        resp, body = self.object_client.get_object(base_container_name,
                                                   object_name)
        self.assertEqual(body, '1')
        # delete object version 1
        resp, _ = self.object_client.delete_object(base_container_name,
                                                   object_name)
        # containers should be empty
        self.assertContainer(base_container_name, '0', '0',
                             vers_container_name)
        self.assertContainer(vers_container_name, '0', '0',
                             'Missing Header')
