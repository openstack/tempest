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

from tempest.lib.services.identity.v3 import domains_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestDomainsClient(base.BaseServiceTest):
    FAKE_CREATE_DOMAIN = {
        "domain": {
            "description": "Domain description",
            "enabled": True,
            "name": "myDomain"
        }
    }

    FAKE_DOMAIN_INFO = {
        "domain": {
            "description": "Used for swift functional testing",
            "enabled": True,
            "id": "5a75994a3",
            "links": {
                "self": "http://example.com/identity/v3/domains/5a75994a3"
            },
            "name": "swift_test"
        }
    }

    FAKE_LIST_DOMAINS = {
        "domains": [
            {
                "description": "Used for swift functional testing",
                "enabled": True,
                "id": "5a75994a3",
                "links": {
                    "self": "http://example.com/identity/v3/domains/5a75994a3"
                },
                "name": "swift_test"
            },
            {
                "description": "Owns users and tenants available on " +
                               "Identity API",
                "enabled": True,
                "id": "default",
                "links": {
                    "self": "http://example.com/identity/v3/domains/default"
                },
                "name": "Default"
            }
        ],
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/domains"
        }
    }

    def setUp(self):
        super(TestDomainsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = domains_client.DomainsClient(fake_auth,
                                                   'identity',
                                                   'regionOne')

    def _test_create_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_domain,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_DOMAIN,
            bytes_body,
            status=201)

    def _test_show_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_DOMAIN_INFO,
            bytes_body,
            domain_id="5a75994a3")

    def _test_list_domains(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_domains,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_DOMAINS,
            bytes_body)

    def _test_update_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_domain,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_DOMAIN_INFO,
            bytes_body,
            domain_id="5a75994a3")

    def test_create_domain_with_str_body(self):
        self._test_create_domain()

    def test_create_domain_with_bytes_body(self):
        self._test_create_domain(bytes_body=True)

    def test_show_domain_with_str_body(self):
        self._test_show_domain()

    def test_show_domain_with_bytes_body(self):
        self._test_show_domain(bytes_body=True)

    def test_list_domain_with_str_body(self):
        self._test_list_domains()

    def test_list_domain_with_bytes_body(self):
        self._test_list_domains(bytes_body=True)

    def test_update_domain_with_str_body(self):
        self._test_update_domain()

    def test_update_domain_with_bytes_body(self):
        self._test_update_domain(bytes_body=True)

    def test_delete_domain(self):
        self.check_service_client_function(
            self.client.delete_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="5a75994a3",
            status=204)
