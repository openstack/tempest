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

from tempest.lib.services.identity.v2 import identity_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestIdentityClient(base.BaseServiceTest):
    FAKE_TOKEN = {
        "tokens": {
            "id": "cbc36478b0bd8e67e89",
            "name": "FakeToken",
            "type": "token",
        }
    }

    FAKE_ENDPOINTS_FOR_TOKEN = {
        "endpoints_links": [],
        "endpoints": [
            {
                "name": "nova",
                "adminURL": "https://nova.region-one.internal.com/" +
                            "v2/be1319401cfa4a0aa590b97cc7b64d8d",
                "region": "RegionOne",
                "internalURL": "https://nova.region-one.internal.com/" +
                               "v2/be1319401cfa4a0aa590b97cc7b64d8d",
                "type": "compute",
                "id": "11b41ee1b00841128b7333d4bf1a6140",
                "publicURL": "https://nova.region-one.public.com/v2/" +
                             "be1319401cfa4a0aa590b97cc7b64d8d"
            },
            {
                "name": "neutron",
                "adminURL": "https://neutron.region-one.internal.com/",
                "region": "RegionOne",
                "internalURL": "https://neutron.region-one.internal.com/",
                "type": "network",
                "id": "cdbfa3c416d741a9b5c968f2dc628acb",
                "publicURL": "https://neutron.region-one.public.com/"
            }
        ]
    }

    FAKE_API_INFO = {
        "name": "API_info",
        "type": "API",
        "description": "test_description"
    }

    FAKE_LIST_EXTENSIONS = {
        "extensions": {
            "values": [
                {
                    "updated": "2013-07-07T12:00:0-00:00",
                    "name": "OpenStack S3 API",
                    "links": [
                        {
                            "href": "https://github.com/openstack/" +
                                    "identity-api",
                            "type": "text/html",
                            "rel": "describedby"
                        }
                    ],
                    "namespace": "http://docs.openstack.org/identity/" +
                                 "api/ext/s3tokens/v1.0",
                    "alias": "s3tokens",
                    "description": "OpenStack S3 API."
                },
                {
                    "updated": "2013-12-17T12:00:0-00:00",
                    "name": "OpenStack Federation APIs",
                    "links": [
                        {
                            "href": "https://github.com/openstack/" +
                                    "identity-api",
                            "type": "text/html",
                            "rel": "describedby"
                        }
                    ],
                    "namespace": "http://docs.openstack.org/identity/" +
                                 "api/ext/OS-FEDERATION/v1.0",
                    "alias": "OS-FEDERATION",
                    "description": "OpenStack Identity Providers Mechanism."
                },
                {
                    "updated": "2014-01-20T12:00:0-00:00",
                    "name": "OpenStack Simple Certificate API",
                    "links": [
                        {
                            "href": "https://github.com/openstack/" +
                                    "identity-api",
                            "type": "text/html",
                            "rel": "describedby"
                        }
                    ],
                    "namespace": "http://docs.openstack.org/identity/api/" +
                                 "ext/OS-SIMPLE-CERT/v1.0",
                    "alias": "OS-SIMPLE-CERT",
                    "description": "OpenStack simple certificate extension"
                },
                {
                    "updated": "2013-07-07T12:00:0-00:00",
                    "name": "OpenStack OAUTH1 API",
                    "links": [
                        {
                            "href": "https://github.com/openstack/" +
                                    "identity-api",
                            "type": "text/html",
                            "rel": "describedby"
                        }
                    ],
                    "namespace": "http://docs.openstack.org/identity/" +
                                 "api/ext/OS-OAUTH1/v1.0",
                    "alias": "OS-OAUTH1",
                    "description": "OpenStack OAuth Delegated Auth Mechanism."
                },
                {
                    "updated": "2013-07-07T12:00:0-00:00",
                    "name": "OpenStack EC2 API",
                    "links": [
                        {
                            "href": "https://github.com/openstack/" +
                                    "identity-api",
                            "type": "text/html",
                            "rel": "describedby"
                        }
                    ],
                    "namespace": "http://docs.openstack.org/identity/api/" +
                                 "ext/OS-EC2/v1.0",
                    "alias": "OS-EC2",
                    "description": "OpenStack EC2 Credentials backend."
                }
            ]
        }
    }

    def setUp(self):
        super(TestIdentityClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = identity_client.IdentityClient(fake_auth,
                                                     'identity',
                                                     'regionOne')

    def _test_show_api_description(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_api_description,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_API_INFO,
            bytes_body)

    def _test_list_extensions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_extensions,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_EXTENSIONS,
            bytes_body)

    def _test_show_token(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_token,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_TOKEN,
            bytes_body,
            token_id="cbc36478b0bd8e67e89")

    def _test_list_endpoints_for_token(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoints_for_token,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ENDPOINTS_FOR_TOKEN,
            bytes_body,
            token_id="cbc36478b0bd8e67e89")

    def _test_check_token_existence(self, bytes_body=False):
        self.check_service_client_function(
            self.client.check_token_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            bytes_body,
            token_id="cbc36478b0bd8e67e89")

    def test_show_api_description_with_str_body(self):
        self._test_show_api_description()

    def test_show_api_description_with_bytes_body(self):
        self._test_show_api_description(bytes_body=True)

    def test_show_list_extensions_with_str_body(self):
        self._test_list_extensions()

    def test_show_list_extensions_with_bytes_body(self):
        self._test_list_extensions(bytes_body=True)

    def test_show_token_with_str_body(self):
        self._test_show_token()

    def test_show_token_with_bytes_body(self):
        self._test_show_token(bytes_body=True)

    def test_list_endpoints_for_token_with_str_body(self):
        self._test_list_endpoints_for_token()

    def test_list_endpoints_for_token_with_bytes_body(self):
        self._test_list_endpoints_for_token(bytes_body=True)

    def test_check_token_existence_with_bytes_body(self):
        self._test_check_token_existence(bytes_body=True)

    def test_check_token_existence_with_str_body(self):
        self._test_check_token_existence()

    def test_delete_token(self):
        self.check_service_client_function(
            self.client.delete_token,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            token_id="cbc36478b0bd8e67e89",
            status=204)
