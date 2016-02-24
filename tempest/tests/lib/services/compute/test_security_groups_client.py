# Copyright 2015 NEC Corporation.  All rights reserved.
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

from oslotest import mockpatch

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import security_groups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestSecurityGroupsClient(base.BaseComputeServiceTest):

    FAKE_SECURITY_GROUP_INFO = [{
        "description": "default",
        "id": "3fb26eb3-581b-4420-9963-b0879a026506",
        "name": "default",
        "rules": [],
        "tenant_id": "openstack"
    }]

    def setUp(self):
        super(TestSecurityGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = security_groups_client.SecurityGroupsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_security_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_security_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            {"security_groups": self.FAKE_SECURITY_GROUP_INFO},
            to_utf=bytes_body)

    def test_list_security_groups_with_str_body(self):
        self._test_list_security_groups()

    def test_list_security_groups_with_bytes_body(self):
        self._test_list_security_groups(bytes_body=True)

    def _test_show_security_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_security_group,
            'tempest.lib.common.rest_client.RestClient.get',
            {"security_group": self.FAKE_SECURITY_GROUP_INFO[0]},
            to_utf=bytes_body,
            security_group_id='fake-id')

    def test_show_security_group_with_str_body(self):
        self._test_show_security_group()

    def test_show_security_group_with_bytes_body(self):
        self._test_show_security_group(bytes_body=True)

    def _test_create_security_group(self, bytes_body=False):
        post_body = {"name": "test", "description": "test_group"}
        self.check_service_client_function(
            self.client.create_security_group,
            'tempest.lib.common.rest_client.RestClient.post',
            {"security_group": self.FAKE_SECURITY_GROUP_INFO[0]},
            to_utf=bytes_body,
            kwargs=post_body)

    def test_create_security_group_with_str_body(self):
        self._test_create_security_group()

    def test_create_security_group_with_bytes_body(self):
        self._test_create_security_group(bytes_body=True)

    def _test_update_security_group(self, bytes_body=False):
        req_body = {"name": "test", "description": "test_group"}
        self.check_service_client_function(
            self.client.update_security_group,
            'tempest.lib.common.rest_client.RestClient.put',
            {"security_group": self.FAKE_SECURITY_GROUP_INFO[0]},
            to_utf=bytes_body,
            security_group_id='fake-id',
            kwargs=req_body)

    def test_update_security_group_with_str_body(self):
        self._test_update_security_group()

    def test_update_security_group_with_bytes_body(self):
        self._test_update_security_group(bytes_body=True)

    def test_delete_security_group(self):
        self.check_service_client_function(
            self.client.delete_security_group,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, security_group_id='fake-id')

    def test_is_resource_deleted_true(self):
        mod = ('tempest.lib.services.compute.security_groups_client.'
               'SecurityGroupsClient.show_security_group')
        self.useFixture(mockpatch.Patch(mod, side_effect=lib_exc.NotFound))
        self.assertTrue(self.client.is_resource_deleted('fake-id'))

    def test_is_resource_deleted_false(self):
        mod = ('tempest.lib.services.compute.security_groups_client.'
               'SecurityGroupsClient.show_security_group')
        self.useFixture(mockpatch.Patch(mod, return_value='success'))
        self.assertFalse(self.client.is_resource_deleted('fake-id'))
