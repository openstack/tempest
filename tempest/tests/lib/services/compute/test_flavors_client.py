# Copyright 2015 IBM Corp.
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

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.lib.services.compute import flavors_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_http
from tempest.tests.lib.services.compute import base


class TestFlavorsClient(base.BaseComputeServiceTest):

    FAKE_FLAVOR = {
        "disk": 1,
        "id": "1",
        "links": [{
            "href": "http://openstack.example.com/v2/openstack/flavors/1",
            "rel": "self"}, {
            "href": "http://openstack.example.com/openstack/flavors/1",
            "rel": "bookmark"}],
        "name": "m1.tiny",
        "ram": 512,
        "swap": 1,
        "vcpus": 1
    }

    EXTRA_SPECS = {"extra_specs": {
        "key1": "value1",
        "key2": "value2"}
    }

    FAKE_FLAVOR_ACCESS = {
        "flavor_id": "10",
        "tenant_id": "1a951d988e264818afe520e78697dcbf"
    }

    def setUp(self):
        super(TestFlavorsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = flavors_client.FlavorsClient(fake_auth,
                                                   'compute', 'regionOne')

    def _test_list_flavors(self, bytes_body=False):
        flavor = copy.deepcopy(TestFlavorsClient.FAKE_FLAVOR)
        # Remove extra attributes
        for attribute in ('disk', 'vcpus', 'ram', 'swap'):
            del flavor[attribute]
        expected = {'flavors': [flavor]}
        self.check_service_client_function(
            self.client.list_flavors,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body)

    def test_list_flavors_str_body(self):
        self._test_list_flavors(bytes_body=False)

    def test_list_flavors_byte_body(self):
        self._test_list_flavors(bytes_body=True)

    def _test_show_flavor(self, bytes_body=False):
        expected = {"flavor": TestFlavorsClient.FAKE_FLAVOR}
        self.check_service_client_function(
            self.client.show_flavor,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body,
            flavor_id='fake-id')

    def test_show_flavor_str_body(self):
        self._test_show_flavor(bytes_body=False)

    def test_show_flavor_byte_body(self):
        self._test_show_flavor(bytes_body=True)

    def _test_create_flavor(self, bytes_body=False):
        expected = {"flavor": TestFlavorsClient.FAKE_FLAVOR}
        request = copy.deepcopy(TestFlavorsClient.FAKE_FLAVOR)
        # The 'links' parameter should not be passed in
        del request['links']
        self.check_service_client_function(
            self.client.create_flavor,
            'tempest.lib.common.rest_client.RestClient.post',
            expected,
            bytes_body,
            **request)

    def test_create_flavor_str_body(self):
        self._test_create_flavor(bytes_body=False)

    def test_create_flavor__byte_body(self):
        self._test_create_flavor(bytes_body=True)

    def test_delete_flavor(self):
        self.check_service_client_function(
            self.client.delete_flavor,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, flavor_id='c782b7a9-33cd-45f0-b795-7f87f456408b')

    def _test_is_resource_deleted(self, flavor_id, is_deleted=True,
                                  bytes_body=False):
        body = json.dumps({'flavors': [TestFlavorsClient.FAKE_FLAVOR]})
        if bytes_body:
            body = body.encode('utf-8')
        response = fake_http.fake_http_response({}, status=200), body
        self.useFixture(mockpatch.Patch(
            'tempest.lib.common.rest_client.RestClient.get',
            return_value=response))
        self.assertEqual(is_deleted,
                         self.client.is_resource_deleted(flavor_id))

    def test_is_resource_deleted_true_str_body(self):
        self._test_is_resource_deleted('2', bytes_body=False)

    def test_is_resource_deleted_true_byte_body(self):
        self._test_is_resource_deleted('2', bytes_body=True)

    def test_is_resource_deleted_false_str_body(self):
        self._test_is_resource_deleted('1', is_deleted=False, bytes_body=False)

    def test_is_resource_deleted_false_byte_body(self):
        self._test_is_resource_deleted('1', is_deleted=False, bytes_body=True)

    def _test_set_flavor_extra_spec(self, bytes_body=False):
        self.check_service_client_function(
            self.client.set_flavor_extra_spec,
            'tempest.lib.common.rest_client.RestClient.post',
            TestFlavorsClient.EXTRA_SPECS,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6',
            **TestFlavorsClient.EXTRA_SPECS)

    def test_set_flavor_extra_spec_str_body(self):
        self._test_set_flavor_extra_spec(bytes_body=False)

    def test_set_flavor_extra_spec_byte_body(self):
        self._test_set_flavor_extra_spec(bytes_body=True)

    def _test_list_flavor_extra_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_flavor_extra_specs,
            'tempest.lib.common.rest_client.RestClient.get',
            TestFlavorsClient.EXTRA_SPECS,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6')

    def test_list_flavor_extra_specs_str_body(self):
        self._test_list_flavor_extra_specs(bytes_body=False)

    def test_list_flavor_extra_specs__byte_body(self):
        self._test_list_flavor_extra_specs(bytes_body=True)

    def _test_show_flavor_extra_spec(self, bytes_body=False):
        expected = {"key": "value"}
        self.check_service_client_function(
            self.client.show_flavor_extra_spec,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6',
            key='key')

    def test_show_flavor_extra_spec_str_body(self):
        self._test_show_flavor_extra_spec(bytes_body=False)

    def test_show_flavor_extra_spec__byte_body(self):
        self._test_show_flavor_extra_spec(bytes_body=True)

    def _test_update_flavor_extra_spec(self, bytes_body=False):
        expected = {"key1": "value"}
        self.check_service_client_function(
            self.client.update_flavor_extra_spec,
            'tempest.lib.common.rest_client.RestClient.put',
            expected,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6',
            key='key1', **expected)

    def test_update_flavor_extra_spec_str_body(self):
        self._test_update_flavor_extra_spec(bytes_body=False)

    def test_update_flavor_extra_spec_byte_body(self):
        self._test_update_flavor_extra_spec(bytes_body=True)

    def test_unset_flavor_extra_spec(self):
        self.check_service_client_function(
            self.client.unset_flavor_extra_spec,
            'tempest.lib.common.rest_client.RestClient.delete', {},
            flavor_id='c782b7a9-33cd-45f0-b795-7f87f456408b', key='key')

    def _test_list_flavor_access(self, bytes_body=False):
        expected = {'flavor_access': [TestFlavorsClient.FAKE_FLAVOR_ACCESS]}
        self.check_service_client_function(
            self.client.list_flavor_access,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6')

    def test_list_flavor_access_str_body(self):
        self._test_list_flavor_access(bytes_body=False)

    def test_list_flavor_access_byte_body(self):
        self._test_list_flavor_access(bytes_body=True)

    def _test_add_flavor_access(self, bytes_body=False):
        expected = {
            "flavor_access": [TestFlavorsClient.FAKE_FLAVOR_ACCESS]
        }
        self.check_service_client_function(
            self.client.add_flavor_access,
            'tempest.lib.common.rest_client.RestClient.post',
            expected,
            bytes_body,
            flavor_id='8c7aae5a-d315-4216-875b-ed9b6a5bcfc6',
            tenant_id='1a951d988e264818afe520e78697dcbf')

    def test_add_flavor_access_str_body(self):
        self._test_add_flavor_access(bytes_body=False)

    def test_add_flavor_access_byte_body(self):
        self._test_add_flavor_access(bytes_body=True)

    def _test_remove_flavor_access(self, bytes_body=False):
        expected = {
            "flavor_access": [TestFlavorsClient.FAKE_FLAVOR_ACCESS]
        }
        self.check_service_client_function(
            self.client.remove_flavor_access,
            'tempest.lib.common.rest_client.RestClient.post',
            expected,
            bytes_body,
            flavor_id='10',
            tenant_id='a6edd4d66ad04245b5d2d8716ecc91e3')

    def test_remove_flavor_access_str_body(self):
        self._test_remove_flavor_access(bytes_body=False)

    def test_remove_flavor_access_byte_body(self):
        self._test_remove_flavor_access(bytes_body=True)
