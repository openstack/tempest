# Copyright 2016 Hewlett Packard Enterprise Development LP
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

from unittest import mock

from tempest.lib.common import cred_client
from tempest.tests import base


class TestCredClientV2(base.TestCase):
    def setUp(self):
        super(TestCredClientV2, self).setUp()
        self.identity_client = mock.MagicMock()
        self.projects_client = mock.MagicMock()
        self.users_client = mock.MagicMock()
        self.roles_client = mock.MagicMock()
        self.creds_client = cred_client.V2CredsClient(self.identity_client,
                                                      self.projects_client,
                                                      self.users_client,
                                                      self.roles_client)

    def test_create_project(self):
        self.projects_client.create_tenant.return_value = {
            'tenant': 'a_tenant'
        }
        res = self.creds_client.create_project('fake_name', 'desc')
        self.assertEqual('a_tenant', res)
        self.projects_client.create_tenant.assert_called_once_with(
            name='fake_name', description='desc')

    def test_delete_project(self):
        self.creds_client.delete_project('fake_id')
        self.projects_client.delete_tenant.assert_called_once_with(
            'fake_id')


class TestCredClientV3(base.TestCase):
    def setUp(self):
        super(TestCredClientV3, self).setUp()
        self.identity_client = mock.MagicMock()
        self.projects_client = mock.MagicMock()
        self.users_client = mock.MagicMock()
        self.roles_client = mock.MagicMock()
        self.domains_client = mock.MagicMock()
        self.domains_client.list_domains.return_value = {
            'domains': [{'id': 'fake_domain_id'}]
        }
        self.creds_client = cred_client.V3CredsClient(self.identity_client,
                                                      self.projects_client,
                                                      self.users_client,
                                                      self.roles_client,
                                                      self.domains_client,
                                                      'fake_domain')

    def test_create_project(self):
        self.projects_client.create_project.return_value = {
            'project': 'a_tenant'
        }
        res = self.creds_client.create_project('fake_name', 'desc')
        self.assertEqual('a_tenant', res)
        self.projects_client.create_project.assert_called_once_with(
            name='fake_name', description='desc', domain_id='fake_domain_id')

    def test_delete_project(self):
        self.creds_client.delete_project('fake_id')
        self.projects_client.delete_project.assert_called_once_with(
            'fake_id')
