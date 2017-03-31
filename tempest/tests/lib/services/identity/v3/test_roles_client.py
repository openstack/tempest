# Copyright 2016 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.identity.v3 import roles_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRolesClient(base.BaseServiceTest):

    FAKE_ROLE_ID = "1"
    FAKE_ROLE_NAME = "test"
    FAKE_DOMAIN_ID = "1"

    FAKE_ROLE_ID_2 = "2"
    FAKE_ROLE_NAME_2 = "test2"

    FAKE_ROLE_ID_3 = "3"
    FAKE_ROLE_NAME_3 = "test3"

    FAKE_ROLE_ID_4 = "4"
    FAKE_ROLE_NAME_4 = "test4"

    FAKE_ROLE_ID_5 = "5"
    FAKE_ROLE_NAME_5 = "test5"

    FAKE_ROLE_ID_6 = "6"
    FAKE_ROLE_NAME_6 = "test6"

    FAKE_ROLE_INFO = {
        "role": {
            "domain_id": FAKE_DOMAIN_ID,
            "id": FAKE_ROLE_ID,
            "name": FAKE_ROLE_NAME,
            "links": {
                "self": "http://example.com/identity/v3/roles/%s" % (
                    FAKE_ROLE_ID)
            }
        }
    }

    FAKE_ROLE_INFO_2 = {
        "role": {
            "domain_id": FAKE_DOMAIN_ID,
            "id": FAKE_ROLE_ID_2,
            "name": FAKE_ROLE_NAME_2,
            "links": {
                "self": "http://example.com/identity/v3/roles/%s" % (
                    FAKE_ROLE_ID_2)
            }
        }
    }

    FAKE_LIST_ROLES = {"roles": [FAKE_ROLE_INFO, FAKE_ROLE_INFO_2]}

    FAKE_ROLE_INFERENCE_RULE = {
        "role_inference": {
            "prior_role": {
                "id": FAKE_ROLE_ID,
                "name": FAKE_ROLE_NAME,
                "links": {
                    "self": "http://example.com/identity/v3/roles/%s" % (
                        FAKE_ROLE_ID)
                }
            },
            "implies": {
                "id": FAKE_ROLE_ID_2,
                "name": FAKE_ROLE_NAME_2,
                "links": {
                    "self": "http://example.com/identity/v3/roles/%s" % (
                        FAKE_ROLE_ID_2)
                }
            }
        },
        "links": {
            "self": "http://example.com/identity/v3/roles/"
                    "%s/implies/%s" % (FAKE_ROLE_ID, FAKE_ROLE_ID_2)
        }
    }

    COMMON_FAKE_LIST_ROLE_INFERENCE_RULES = [
        {
            "prior_role": {
                "id": FAKE_ROLE_ID,
                "name": FAKE_ROLE_NAME,
                "links": {
                    "self": "http://example.com/identity/v3/roles/%s" % (
                        FAKE_ROLE_ID)
                }
            },
            "implies": [
                {
                    "id": FAKE_ROLE_ID_2,
                    "name": FAKE_ROLE_NAME_2,
                    "links": {
                        "self": "http://example.com/identity/v3/roles/%s" % (
                            FAKE_ROLE_ID_2)
                    }
                },
                {
                    "id": FAKE_ROLE_ID_3,
                    "name": FAKE_ROLE_NAME_3,
                    "links": {
                        "self": "http://example.com/identity/v3/roles/%s" % (
                            FAKE_ROLE_ID_3)
                    }
                }
            ]
        },
        {
            "prior_role": {
                "id": FAKE_ROLE_ID_4,
                "name": FAKE_ROLE_NAME_4,
                "links": {
                    "self": "http://example.com/identity/v3/roles/%s" % (
                        FAKE_ROLE_ID_4)
                }
            },
            "implies": [
                {
                    "id": FAKE_ROLE_ID_5,
                    "name": FAKE_ROLE_NAME_5,
                    "links": {
                        "self": "http://example.com/identity/v3/roles/%s" % (
                            FAKE_ROLE_ID_5)
                    }
                },
                {
                    "id": FAKE_ROLE_ID_6,
                    "name": FAKE_ROLE_NAME_6,
                    "links": {
                        "self": "http://example.com/identity/v3/roles/%s" % (
                            FAKE_ROLE_ID_6)
                    }
                }
            ]
        }
    ]

    FAKE_LIST_ROLE_INFERENCE_RULES = {
        "role_inference": COMMON_FAKE_LIST_ROLE_INFERENCE_RULES[0],
        "links": {
            "self": "http://example.com/identity/v3/roles/"
                    "%s/implies" % FAKE_ROLE_ID
        }
    }

    FAKE_LIST_ALL_ROLE_INFERENCE_RULES = {
        "role_inferences": COMMON_FAKE_LIST_ROLE_INFERENCE_RULES,
        "links": {
            "self": "http://example.com/identity/v3/role_inferences"
        }
    }

    def setUp(self):
        super(TestRolesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = roles_client.RolesClient(fake_auth,
                                               'identity', 'regionOne')

    def _test_create_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_role,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_ROLE_INFO,
            bytes_body,
            domain_id=self.FAKE_DOMAIN_ID,
            name=self.FAKE_ROLE_NAME,
            status=201)

    def _test_show_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_role,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ROLE_INFO,
            bytes_body,
            role_id=self.FAKE_ROLE_ID)

    def _test_list_roles(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_roles,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body)

    def _test_update_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_role,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_ROLE_INFO,
            bytes_body,
            role_id=self.FAKE_ROLE_ID,
            name=self.FAKE_ROLE_NAME)

    def _test_create_user_role_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_role_on_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_create_user_role_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_list_user_roles_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_roles_on_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def _test_list_user_roles_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_roles_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def _test_create_group_role_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_role_on_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def _test_create_group_role_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def _test_list_group_roles_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_roles_on_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123")

    def _test_list_group_roles_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_roles_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123")

    def _test_create_role_inference_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_role_inference_rule,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_ROLE_INFERENCE_RULE,
            bytes_body,
            status=201,
            prior_role=self.FAKE_ROLE_ID,
            implies_role=self.FAKE_ROLE_ID_2)

    def _test_show_role_inference_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_role_inference_rule,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ROLE_INFERENCE_RULE,
            bytes_body,
            prior_role=self.FAKE_ROLE_ID,
            implies_role=self.FAKE_ROLE_ID_2)

    def _test_list_role_inferences_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_role_inferences_rules,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLE_INFERENCE_RULES,
            bytes_body,
            prior_role=self.FAKE_ROLE_ID)

    def _test_list_all_role_inference_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_all_role_inference_rules,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ALL_ROLE_INFERENCE_RULES,
            bytes_body)

    def test_create_role_with_str_body(self):
        self._test_create_role()

    def test_create_role_with_bytes_body(self):
        self._test_create_role(bytes_body=True)

    def test_show_role_with_str_body(self):
        self._test_show_role()

    def test_show_role_with_bytes_body(self):
        self._test_show_role(bytes_body=True)

    def test_list_roles_with_str_body(self):
        self._test_list_roles()

    def test_list_roles_with_bytes_body(self):
        self._test_list_roles(bytes_body=True)

    def test_update_role_with_str_body(self):
        self._test_update_role()

    def test_update_role_with_bytes_body(self):
        self._test_update_role(bytes_body=True)

    def test_delete_role(self):
        self.check_service_client_function(
            self.client.delete_role,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            role_id=self.FAKE_ROLE_ID,
            status=204)

    def test_create_user_role_on_project_with_str_body(self):
        self._test_create_user_role_on_project()

    def test_create_user_role_on_project_with_bytes_body(self):
        self._test_create_user_role_on_project(bytes_body=True)

    def test_create_user_role_on_domain_with_str_body(self):
        self._test_create_user_role_on_domain()

    def test_create_user_role_on_domain_with_bytes_body(self):
        self._test_create_user_role_on_domain(bytes_body=True)

    def test_create_group_role_on_domain_with_str_body(self):
        self._test_create_group_role_on_domain()

    def test_create_group_role_on_domain_with_bytes_body(self):
        self._test_create_group_role_on_domain(bytes_body=True)

    def test_list_user_roles_on_project_with_str_body(self):
        self._test_list_user_roles_on_project()

    def test_list_user_roles_on_project_with_bytes_body(self):
        self._test_list_user_roles_on_project(bytes_body=True)

    def test_list_user_roles_on_domain_with_str_body(self):
        self._test_list_user_roles_on_domain()

    def test_list_user_roles_on_domain_with_bytes_body(self):
        self._test_list_user_roles_on_domain(bytes_body=True)

    def test_list_group_roles_on_domain_with_str_body(self):
        self._test_list_group_roles_on_domain()

    def test_list_group_roles_on_domain_with_bytes_body(self):
        self._test_list_group_roles_on_domain(bytes_body=True)

    def test_delete_role_from_user_on_project(self):
        self.check_service_client_function(
            self.client.delete_role_from_user_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_user_on_domain(self):
        self.check_service_client_function(
            self.client.delete_role_from_user_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_group_on_project(self):
        self.check_service_client_function(
            self.client.delete_role_from_group_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_group_on_domain(self):
        self.check_service_client_function(
            self.client.delete_role_from_group_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_user_role_existence_on_project(self):
        self.check_service_client_function(
            self.client.check_user_role_existence_on_project,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_user_role_existence_on_domain(self):
        self.check_service_client_function(
            self.client.check_user_role_existence_on_domain,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_role_from_group_on_project_existence(self):
        self.check_service_client_function(
            self.client.check_role_from_group_on_project_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_role_from_group_on_domain_existence(self):
        self.check_service_client_function(
            self.client.check_role_from_group_on_domain_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_create_role_inference_rule_with_str_body(self):
        self._test_create_role_inference_rule()

    def test_create_role_inference_rule_with_bytes_body(self):
        self._test_create_role_inference_rule(bytes_body=True)

    def test_show_role_inference_rule_with_str_body(self):
        self._test_show_role_inference_rule()

    def test_show_role_inference_rule_with_bytes_body(self):
        self._test_show_role_inference_rule(bytes_body=True)

    def test_list_role_inferences_rules_with_str_body(self):
        self._test_list_role_inferences_rules()

    def test_list_role_inferences_rules_with_bytes_body(self):
        self._test_list_role_inferences_rules(bytes_body=True)

    def test_check_role_inference_rule(self):
        self.check_service_client_function(
            self.client.check_role_inference_rule,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            status=204,
            prior_role=self.FAKE_ROLE_ID,
            implies_role=self.FAKE_ROLE_ID_2)

    def test_delete_role_inference_rule(self):
        self.check_service_client_function(
            self.client.delete_role_inference_rule,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            prior_role=self.FAKE_ROLE_ID,
            implies_role=self.FAKE_ROLE_ID_2)

    def test_list_all_role_inference_rules_with_str_body(self):
        self._test_list_all_role_inference_rules()

    def test_list_all_role_inference_rules_with_bytes_body(self):
        self._test_list_all_role_inference_rules(bytes_body=True)
