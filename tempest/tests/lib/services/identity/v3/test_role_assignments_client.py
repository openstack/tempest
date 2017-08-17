# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import role_assignments_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRoleAssignmentsClient(base.BaseServiceTest):

    FAKE_USER_ID = "313234"
    FAKE_GROUP_ID = "101112"

    FAKE_ROLE1_ID = "123456"
    FAKE_ROLE2_ID = "123457"

    FAKE_PROJECT_ID = "456789"
    FAKE_DOMAIN_ID = "102030"

    FAKE_USER_PROJECT_ASSIGNMENT = {
        "links": {
            "assignment": "http://example.com/identity/v3/projects/"
                          "%s/users/%s/roles/%s" % (FAKE_PROJECT_ID,
                                                    FAKE_USER_ID,
                                                    FAKE_ROLE2_ID)
        },
        "role": {
            "id": FAKE_ROLE2_ID
        },
        "scope": {
            "project": {
                "id": FAKE_PROJECT_ID
            }
        },
        "user": {
            "id": FAKE_USER_ID
        }
    }

    FAKE_GROUP_PROJECT_ASSIGNMENT = {
        "links": {
            "assignment": "http://example.com/identity/v3/projects/"
                          "%s/groups/%s/roles/%s" % (FAKE_PROJECT_ID,
                                                     FAKE_GROUP_ID,
                                                     FAKE_ROLE1_ID)
        },
        "role": {
            "id": FAKE_ROLE1_ID
        },
        "scope": {
            "project": {
                "id": FAKE_PROJECT_ID
            }
        },
        "group": {
            "id": FAKE_GROUP_ID
        }
    }

    FAKE_USER_PROJECT_EFFECTIVE_ASSIGNMENT = {
        "links": {
            "assignment": "http://example.com/identity/v3/projects/"
                          "%s/groups/%s/roles/%s" % (FAKE_PROJECT_ID,
                                                     FAKE_GROUP_ID,
                                                     FAKE_ROLE1_ID),
            "membership": "http://example.com/identity/v3/groups/"
                          "%s/users/%s" % (FAKE_GROUP_ID, FAKE_USER_ID)
        },
        "role": {
            "id": FAKE_ROLE1_ID
        },
        "scope": {
            "project": {
                "id": FAKE_PROJECT_ID
            }
        },
        "user": {
            "id": FAKE_USER_ID
        }
    }

    FAKE_USER_DOMAIN_ASSIGNMENT = {
        "links": {
            "assignment": "http://example.com/identity/v3/domains/"
                          "%s/users/%s/roles/%s" % (FAKE_DOMAIN_ID,
                                                    FAKE_USER_ID,
                                                    FAKE_ROLE1_ID)
        },
        "role": {
            "id": FAKE_ROLE1_ID
        },
        "scope": {
            "domain": {
                "id": FAKE_DOMAIN_ID
            }
        },
        "user": {
            "id": FAKE_USER_ID
        }
    }

    FAKE_GROUP_PROJECT_ASSIGNMENTS = {
        "role_assignments": [
            FAKE_GROUP_PROJECT_ASSIGNMENT
        ],
        "links": {
            "self": "http://example.com/identity/v3/role_assignments?"
                    "scope.project.id=%s&group.id=%s&effective" % (
                        FAKE_PROJECT_ID, FAKE_GROUP_ID),
            "previous": None,
            "next": None
        }
    }

    FAKE_USER_PROJECT_EFFECTIVE_ASSIGNMENTS = {
        "role_assignments": [
            FAKE_USER_PROJECT_ASSIGNMENT,
            FAKE_USER_PROJECT_EFFECTIVE_ASSIGNMENT
        ],
        "links": {
            "self": "http://example.com/identity/v3/role_assignments?"
                    "scope.project.id=%s&user.id=%s&effective" % (
                        FAKE_PROJECT_ID, FAKE_USER_ID),
            "previous": None,
            "next": None
        }
    }

    FAKE_USER_DOMAIN_ASSIGNMENTS = {
        "role_assignments": [
            FAKE_USER_DOMAIN_ASSIGNMENT
        ],
        "links": {
            "self": "http://example.com/identity/v3/role_assignments?"
                    "scope.domain.id=%s&user.id=%s&effective" % (
                        FAKE_DOMAIN_ID, FAKE_USER_ID),
            "previous": None,
            "next": None
        }
    }

    def setUp(self):
        super(TestRoleAssignmentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = role_assignments_client.RoleAssignmentsClient(
            fake_auth, 'identity', 'regionOne')

    def _test_list_user_project_effective_assignments(self, bytes_body=False):
        params = {'scope.project.id': self.FAKE_PROJECT_ID,
                  'user.id': self.FAKE_USER_ID}
        self.check_service_client_function(
            self.client.list_role_assignments,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_PROJECT_EFFECTIVE_ASSIGNMENTS,
            bytes_body,
            effective=True,
            **params)

    def test_list_user_project_effective_assignments_with_str_body(self):
        self._test_list_user_project_effective_assignments()

    def test_list_user_project_effective_assignments_with_bytes_body(self):
        self._test_list_user_project_effective_assignments(bytes_body=True)

    def _test_list_group_project_assignments(self, bytes_body=False):
        params = {'scope.project.id': self.FAKE_PROJECT_ID,
                  'group.id': self.FAKE_GROUP_ID}
        self.check_service_client_function(
            self.client.list_role_assignments,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_GROUP_PROJECT_ASSIGNMENTS,
            bytes_body,
            **params)

    def test_list_group_project_assignments_with_str_body(self):
        self._test_list_group_project_assignments()

    def test_list_group_project_assignments_with_bytes_body(self):
        self._test_list_group_project_assignments(bytes_body=True)

    def _test_list_user_domain_assignments(self, bytes_body=False):
        params = {'scope.domain.id': self.FAKE_DOMAIN_ID,
                  'user.id': self.FAKE_USER_ID}
        self.check_service_client_function(
            self.client.list_role_assignments,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_GROUP_PROJECT_ASSIGNMENTS,
            bytes_body,
            **params)

    def test_list_user_domain_assignments_with_str_body(self):
        self._test_list_user_domain_assignments()

    def test_list_user_domain_assignments_with_bytes_body(self):
        self._test_list_user_domain_assignments(bytes_body=True)
