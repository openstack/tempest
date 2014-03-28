# -*- coding: utf-8 -*-
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Chmouel Boudjnah <chmouel@enovance.com>
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
from tempest.api.orchestration import base
from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import test


CONF = config.CONF


class SwiftResourcesTestJSON(base.BaseOrchestrationTest):
    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(SwiftResourcesTestJSON, cls).setUpClass()
        cls.client = cls.orchestration_client
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.load_template('swift_basic')
        os = clients.Manager()
        if not CONF.service_available.swift:
            raise cls.skipException("Swift support is required")
        cls.account_client = os.account_client
        cls.container_client = os.container_client
        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template)
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
        cls.test_resources = {}
        _, resources = cls.client.list_resources(cls.stack_identifier)
        for resource in resources:
            cls.test_resources[resource['logical_resource_id']] = resource

    def test_created_resources(self):
        """Created stack should be in the list of existing stacks."""
        resources = [('SwiftContainer', 'OS::Swift::Container'),
                     ('SwiftContainerWebsite', 'OS::Swift::Container')]
        for resource_name, resource_type in resources:
            resource = self.test_resources.get(resource_name)
            self.assertIsInstance(resource, dict)
            self.assertEqual(resource_type, resource['resource_type'])
            self.assertEqual(resource_name, resource['logical_resource_id'])
            self.assertEqual('CREATE_COMPLETE', resource['resource_status'])

    def test_created_containers(self):
        params = {'format': 'json'}
        resp, container_list = \
            self.account_client.list_account_containers(params=params)
        self.assertEqual('200', resp['status'])
        self.assertEqual(2, len(container_list))
        for cont in container_list:
            self.assertTrue(cont['name'].startswith(self.stack_name))

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

    def test_metadata(self):
        metadatas = {
            "web-index": "index.html",
            "web-error": "error.html"
        }
        swcont_website = self.test_resources.get(
            'SwiftContainerWebsite')['physical_resource_id']
        headers, _ = self.container_client.list_container_metadata(
            swcont_website)

        for meta in metadatas:
            header_meta = "x-container-meta-%s" % meta
            self.assertIn(header_meta, headers)
            self.assertEqual(headers[header_meta], metadatas[meta])
