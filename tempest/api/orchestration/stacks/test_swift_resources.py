# -*- coding: utf-8 -*-
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import clients
from tempest import config
from tempest import test


CONF = config.CONF


class SwiftResourcesTestJSON(base.BaseOrchestrationTest):
    @classmethod
    def skip_checks(cls):
        super(SwiftResourcesTestJSON, cls).skip_checks()
        if not CONF.service_available.swift:
            raise cls.skipException("Swift support is required")

    @classmethod
    def setup_credentials(cls):
        super(SwiftResourcesTestJSON, cls).setup_credentials()
        cls.os = clients.Manager()

    @classmethod
    def setup_clients(cls):
        super(SwiftResourcesTestJSON, cls).setup_clients()
        cls.account_client = cls.os.account_client
        cls.container_client = cls.os.container_client

    @classmethod
    def resource_setup(cls):
        super(SwiftResourcesTestJSON, cls).resource_setup()
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.read_template('swift_basic')
        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template)
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
        cls.test_resources = {}
        resources = cls.client.list_resources(cls.stack_identifier)
        for resource in resources:
            cls.test_resources[resource['logical_resource_id']] = resource

    @test.idempotent_id('1a6fe69e-4be4-4990-9a7a-84b6f18019cb')
    def test_created_resources(self):
        """Created stack should be in the list of existing stacks."""
        swift_basic_template = self.load_template('swift_basic')
        resources = [('SwiftContainer', swift_basic_template['resources'][
                      'SwiftContainer']['type']),
                     ('SwiftContainerWebsite', swift_basic_template[
                      'resources']['SwiftContainerWebsite']['type'])]
        for resource_name, resource_type in resources:
            resource = self.test_resources.get(resource_name)
            self.assertIsInstance(resource, dict)
            self.assertEqual(resource_type, resource['resource_type'])
            self.assertEqual(resource_name, resource['logical_resource_id'])
            self.assertEqual('CREATE_COMPLETE', resource['resource_status'])

    @test.idempotent_id('bd438b18-5494-4d5a-9ce6-d2a942ec5060')
    @test.services('object_storage')
    def test_created_containers(self):
        params = {'format': 'json'}
        _, container_list = \
            self.account_client.list_account_containers(params=params)
        created_containers = [cont for cont in container_list
                              if cont['name'].startswith(self.stack_name)]
        self.assertEqual(2, len(created_containers))

    @test.idempotent_id('73d0c093-9922-44a0-8b1d-1fc092dee367')
    @test.services('object_storage')
    def test_acl(self):
        acl_headers = ('x-container-meta-web-index', 'x-container-read')

        swcont = self.test_resources.get(
            'SwiftContainer')['physical_resource_id']
        swcont_website = self.test_resources.get(
            'SwiftContainerWebsite')['physical_resource_id']

        headers, _ = self.container_client.list_container_metadata(swcont)
        for h in acl_headers:
            self.assertNotIn(h, headers)
        headers, _ = self.container_client.list_container_metadata(
            swcont_website)
        for h in acl_headers:
            self.assertIn(h, headers)

    @test.idempotent_id('fda06135-6777-4594-aefa-0f6107169698')
    @test.services('object_storage')
    def test_metadata(self):
        swift_basic_template = self.load_template('swift_basic')
        metadatas = swift_basic_template['resources']['SwiftContainerWebsite'][
            'properties']['X-Container-Meta']
        swcont_website = self.test_resources.get(
            'SwiftContainerWebsite')['physical_resource_id']
        headers, _ = self.container_client.list_container_metadata(
            swcont_website)

        for meta in metadatas:
            header_meta = "x-container-meta-%s" % meta
            self.assertIn(header_meta, headers)
            self.assertEqual(headers[header_meta], metadatas[meta])
