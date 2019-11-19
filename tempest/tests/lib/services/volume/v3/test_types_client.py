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

from tempest.lib.services.volume.v3 import types_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTypesClient(base.BaseServiceTest):
    FAKE_CREATE_VOLUME_TYPE = {
        'volume_type': {
            'id': '6685584b-1eac-4da6-b5c3-555430cf68ff',
            'name': 'vol-type-001',
            'description': 'volume type 0001',
            'is_public': True,
            'os-volume-type-access:is_public': True,
            'extra_specs': {
                'volume_backend_name': 'rbd'
            }
        }
    }

    FAKE_DEFAULT_VOLUME_TYPE_INFO = {
        'volume_type': {
            'id': '6685584b-1eac-4da6-b5c3-555430cf68ff',
            'qos_specs_id': None,
            'name': 'volume-type-test',
            'description': 'default volume type',
            'is_public': True,
            'os-volume-type-access:is_public': True,
            'extra_specs': {
                'volume_backend_name': 'rbd'
            }
        }
    }

    FAKE_UPDATE_VOLUME_TYPE = {
        'volume_type': {
            'id': '6685584b-1eac-4da6-b5c3-555430cf68ff',
            'name': 'volume-type-test',
            'description': 'default volume type',
            'is_public': True,
            'extra_specs': {
                'volume_backend_name': 'rbd'
            }
        }
    }

    FAKE_VOLUME_TYPES = {
        'volume_types': [
            {
                'name': 'volume_type01',
                'qos_specs_id': None,
                'extra_specs': {
                    'volume_backend_name': 'lvmdriver-1'
                },
                'os-volume-type-access:is_public': True,
                'is_public': True,
                'id': '6685584b-1eac-4da6-b5c3-555430cf68ff',
                'description': None
            },
            {
                'name': 'volume_type02',
                'qos_specs_id': None,
                'extra_specs': {
                    'volume_backend_name': 'lvmdriver-1'
                },
                'os-volume-type-access:is_public': True,
                'is_public': True,
                'id': '8eb69a46-df97-4e41-9586-9a40a7533803',
                'description': None
            }
        ]
    }

    FAKE_VOLUME_TYPE_EXTRA_SPECS = {
        'extra_specs': {
            'capabilities': 'gpu'
        }
    }

    FAKE_SHOW_VOLUME_TYPE_EXTRA_SPECS = {
        'capabilities': 'gpu'
    }

    FAKE_VOLUME_TYPE_ACCESS = {
        'volume_type_access': [{
            'volume_type_id': '3c67e124-39ad-4ace-a507-8bb7bf510c26',
            'project_id': 'f270b245cb11498ca4031deb7e141cfa'
        }]
    }

    def setUp(self):
        super(TestTypesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = types_client.TypesClient(fake_auth,
                                               'volume',
                                               'regionOne')

    def _test_list_volume_types(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_volume_types,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUME_TYPES,
            bytes_body)

    def _test_show_volume_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_volume_type,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_DEFAULT_VOLUME_TYPE_INFO,
            to_utf=bytes_body,
            volume_type_id="6685584b-1eac-4da6-b5c3-555430cf68ff")

    def _test_create_volume_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_volume_type,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_VOLUME_TYPE,
            to_utf=bytes_body,
            name='volume-type-test')

    def _test_delete_volume_type(self):
        self.check_service_client_function(
            self.client.delete_volume_type,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff')

    def _test_list_volume_types_extra_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_volume_types_extra_specs,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUME_TYPE_EXTRA_SPECS,
            to_utf=bytes_body,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff')

    def _test_show_volume_type_extra_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_volume_type_extra_specs,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_VOLUME_TYPE_EXTRA_SPECS,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff',
            extra_specs_name='capabilities',
            to_utf=bytes_body)

    def _test_create_volume_type_extra_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_volume_type_extra_specs,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_VOLUME_TYPE_EXTRA_SPECS,
            volume_type_id="6685584b-1eac-4da6-b5c3-555430cf68ff",
            extra_specs=self.FAKE_VOLUME_TYPE_EXTRA_SPECS,
            to_utf=bytes_body)

    def _test_delete_volume_type_extra_specs(self):
        self.check_service_client_function(
            self.client.delete_volume_type_extra_specs,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff',
            extra_spec_name='volume_backend_name')

    def _test_update_volume_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_volume_type,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_VOLUME_TYPE,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff',
            to_utf=bytes_body,
            name='update-volume-type-test',
            description='test update volume type description')

    def _test_update_volume_type_extra_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_volume_type_extra_specs,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_SHOW_VOLUME_TYPE_EXTRA_SPECS,
            extra_spec_name='capabilities',
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff',
            extra_specs=self.FAKE_SHOW_VOLUME_TYPE_EXTRA_SPECS,
            to_utf=bytes_body)

    def _test_add_type_access(self):
        self.check_service_client_function(
            self.client.add_type_access,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, status=202,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff')

    def _test_remove_type_access(self):
        self.check_service_client_function(
            self.client.remove_type_access,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, status=202,
            volume_type_id='6685584b-1eac-4da6-b5c3-555430cf68ff')

    def _test_list_type_access(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_type_access,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUME_TYPE_ACCESS,
            volume_type_id='3c67e124-39ad-4ace-a507-8bb7bf510c26',
            to_utf=bytes_body)

    def test_list_volume_types_with_str_body(self):
        self._test_list_volume_types()

    def test_list_volume_types_with_bytes_body(self):
        self._test_list_volume_types(bytes_body=True)

    def test_show_volume_type_with_str_body(self):
        self._test_show_volume_type()

    def test_show_volume_type_with_bytes_body(self):
        self._test_show_volume_type(bytes_body=True)

    def test_create_volume_type_str_body(self):
        self._test_create_volume_type()

    def test_create_volume_type_with_bytes_body(self):
        self._test_create_volume_type(bytes_body=True)

    def test_list_volume_types_extra_specs_with_str_body(self):
        self._test_list_volume_types_extra_specs()

    def test_list_volume_types_extra_specs_with_bytes_body(self):
        self._test_list_volume_types_extra_specs(bytes_body=True)

    def test_show_volume_type_extra_specs_with_str_body(self):
        self._test_show_volume_type_extra_specs()

    def test_show_volume_type_extra_specs_with_bytes_body(self):
        self._test_show_volume_type_extra_specs(bytes_body=True)

    def test_create_volume_type_extra_specs_with_str_body(self):
        self._test_create_volume_type_extra_specs()

    def test_create_volume_type_extra_specs_with_bytes_body(self):
        self._test_create_volume_type_extra_specs(bytes_body=True)

    def test_delete_volume_type_extra_specs(self):
        self._test_delete_volume_type_extra_specs()

    def test_update_volume_type_with_str_body(self):
        self._test_update_volume_type()

    def test_update_volume_type_with_bytes_body(self):
        self._test_update_volume_type(bytes_body=True)

    def test_delete_volume_type(self):
        self._test_delete_volume_type()

    def test_update_volume_type_extra_specs_with_str_body(self):
        self._test_update_volume_type_extra_specs()

    def test_update_volume_type_extra_specs_with_bytes_body(self):
        self._test_update_volume_type_extra_specs(bytes_body=True)

    def test_add_type_access(self):
        self._test_add_type_access()

    def test_remove_type_access(self):
        self._test_remove_type_access()

    def test_list_type_access_with_str_body(self):
        self._test_list_type_access()

    def test_list_type_access_with_bytes_body(self):
        self._test_list_type_access(bytes_body=True)
