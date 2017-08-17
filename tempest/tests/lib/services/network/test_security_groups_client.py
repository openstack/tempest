# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

import copy

import mock
from oslo_serialization import jsonutils as json

from tempest.lib.services.network import base as network_base
from tempest.lib.services.network import security_groups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSecurityGroupsClient(base.BaseServiceTest):

    FAKE_SEC_GROUP_ID = "85cc3048-abc3-43cc-89b3-377341426ac5"

    FAKE_SECURITY_GROUPS = {
        "security_groups": [
            {
                "description": "default",
                "id": FAKE_SEC_GROUP_ID,
                "name": "fake-security-group-name",
                "security_group_rules": [
                    {
                        "direction": "egress",
                        "ethertype": "IPv4",
                        "id": "38ce2d8e-e8f1-48bd-83c2-d33cb9f50c3d",
                        "port_range_max": None,
                        "port_range_min": None,
                        "protocol": None,
                        "remote_group_id": None,
                        "remote_ip_prefix": None,
                        "security_group_id": FAKE_SEC_GROUP_ID,
                        "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "description": ""
                    },
                    {
                        "direction": "egress",
                        "ethertype": "IPv6",
                        "id": "565b9502-12de-4ffd-91e9-68885cff6ae1",
                        "port_range_max": None,
                        "port_range_min": None,
                        "protocol": None,
                        "remote_group_id": None,
                        "remote_ip_prefix": None,
                        "security_group_id": FAKE_SEC_GROUP_ID,
                        "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "description": ""
                    }
                ],
                "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550"
            }
        ]
    }

    FAKE_SECURITY_GROUP = {
        "security_group": copy.deepcopy(
            FAKE_SECURITY_GROUPS["security_groups"][0])
    }

    def setUp(self):
        super(TestSecurityGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = security_groups_client.SecurityGroupsClient(
            fake_auth, 'network', 'regionOne')

    def _test_list_security_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_security_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SECURITY_GROUPS,
            bytes_body,
            mock_args='v2.0/security-groups')

    def _test_create_security_group(self, bytes_body=False):
        kwargs = {'name': 'fake-security-group-name'}
        payload = json.dumps({"security_group": kwargs}, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(network_base.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.create_security_group,
                'tempest.lib.common.rest_client.RestClient.post',
                self.FAKE_SECURITY_GROUP,
                bytes_body,
                status=201,
                mock_args=['v2.0/security-groups', payload],
                **kwargs)

    def _test_show_security_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_security_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SECURITY_GROUP,
            bytes_body,
            security_group_id=self.FAKE_SEC_GROUP_ID,
            mock_args='v2.0/security-groups/%s' % self.FAKE_SEC_GROUP_ID)

    def _test_update_security_group(self, bytes_body=False):
        kwargs = {'name': 'updated-security-group-name'}
        resp_body = copy.deepcopy(self.FAKE_SECURITY_GROUP)
        resp_body["security_group"]["name"] = 'updated-security-group-name'

        payload = json.dumps({'security_group': kwargs}, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(network_base.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.update_security_group,
                'tempest.lib.common.rest_client.RestClient.put',
                resp_body,
                bytes_body,
                security_group_id=self.FAKE_SEC_GROUP_ID,
                mock_args=['v2.0/security-groups/%s' % self.FAKE_SEC_GROUP_ID,
                           payload],
                **kwargs)

    def test_list_security_groups_with_str_body(self):
        self._test_list_security_groups()

    def test_list_security_groups_with_bytes_body(self):
        self._test_list_security_groups(bytes_body=True)

    def test_create_security_group_with_str_body(self):
        self._test_create_security_group()

    def test_create_security_group_with_bytes_body(self):
        self._test_create_security_group(bytes_body=True)

    def test_show_security_group_with_str_body(self):
        self._test_show_security_group()

    def test_show_security_group_with_bytes_body(self):
        self._test_show_security_group(bytes_body=True)

    def test_update_security_group_with_str_body(self):
        self._test_update_security_group()

    def test_update_security_group_with_bytes_body(self):
        self._test_update_security_group(bytes_body=True)

    def test_delete_security_group(self):
        self.check_service_client_function(
            self.client.delete_security_group,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            security_group_id=self.FAKE_SEC_GROUP_ID,
            mock_args='v2.0/security-groups/%s' % self.FAKE_SEC_GROUP_ID)
