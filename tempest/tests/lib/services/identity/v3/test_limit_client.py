# Copyright 2021 Red Hat, Inc.
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

from tempest.lib.services.identity.v3 import limits_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestLimitsClient(base.BaseServiceTest):
    def setUp(self):
        super(TestLimitsClient, self).setUp()
        self.client = limits_client.LimitsClient(
            fake_auth_provider.FakeAuthProvider(),
            'identity', 'regionOne')

    def test_get_registered_limits(self):
        fake_result = {'foo': 'bar'}
        self.check_service_client_function(
            self.client.get_registered_limits,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_result,
            False,
            status=200)

    def test_create_limit(self):
        fake_result = {'foo': 'bar'}
        self.check_service_client_function(
            self.client.create_limit,
            'tempest.lib.common.rest_client.RestClient.post',
            fake_result,
            False,
            region_id='regionOne', service_id='image',
            project_id='project', resource_name='widgets',
            default_limit=10,
            description='Spacely Widgets',
            status=201)

    def test_create_limit_with_domain(self):
        fake_result = {'foo': 'bar'}
        self.check_service_client_function(
            self.client.create_limit,
            'tempest.lib.common.rest_client.RestClient.post',
            fake_result,
            False,
            region_id='regionOne', service_id='image',
            project_id='project', resource_name='widgets',
            default_limit=10,
            domain_id='foo',
            description='Spacely Widgets',
            status=201)

    def test_update_limit(self):
        fake_result = {'foo': 'bar'}
        self.check_service_client_function(
            self.client.update_limit,
            'tempest.lib.common.rest_client.RestClient.patch',
            fake_result,
            False,
            limit_id='123', resource_limit=20,
            status=200)

    def test_update_limit_with_description(self):
        fake_result = {'foo': 'bar'}
        self.check_service_client_function(
            self.client.update_limit,
            'tempest.lib.common.rest_client.RestClient.patch',
            fake_result,
            False,
            limit_id='123', resource_limit=20,
            description='new description',
            status=200)
