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

import mock
import random
import six

from tempest.services.identity.v2.json import identity_client as \
    identity_v2_identity_client
from tempest.services.identity.v3.json import credentials_client
from tempest.services.identity.v3.json import endpoints_client
from tempest.services.identity.v3.json import identity_client as \
    identity_v3_identity_client
from tempest.services.identity.v3.json import policies_client
from tempest.services.identity.v3.json import regions_client
from tempest.services.identity.v3.json import services_client
from tempest.services.network.json import network_client
from tempest.tests import base


class TestServiceClient(base.TestCase):

    @mock.patch('tempest.lib.common.rest_client.RestClient.__init__')
    def test_service_client_creations_with_specified_args(self, mock_init):
        test_clients = [
            network_client.NetworkClient,
            identity_v2_identity_client.IdentityClient,
            credentials_client.CredentialsClient,
            endpoints_client.EndPointClient,
            identity_v3_identity_client.IdentityClient,
            policies_client.PoliciesClient,
            regions_client.RegionsClient,
            services_client.ServicesClient,
        ]

        for client in test_clients:
            fake_string = six.text_type(random.randint(1, 0x7fffffff))
            auth = 'auth' + fake_string
            service = 'service' + fake_string
            region = 'region' + fake_string
            params = {
                'endpoint_type': 'URL' + fake_string,
                'build_interval': random.randint(1, 100),
                'build_timeout': random.randint(1, 100),
                'disable_ssl_certificate_validation':
                    True if random.randint(0, 1) else False,
                'ca_certs': None,
                'trace_requests': 'foo' + fake_string
            }
            client(auth, service, region, **params)
            mock_init.assert_called_once_with(auth, service, region, **params)
            mock_init.reset_mock()
