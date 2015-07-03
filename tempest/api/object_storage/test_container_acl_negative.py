# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.object_storage import base
from tempest import config
from tempest import test

CONF = config.CONF


class ObjectACLsNegativeTest(base.BaseObjectTest):

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['operator_alt', CONF.object_storage.operator_role]]

    @classmethod
    def setup_credentials(cls):
        super(ObjectACLsNegativeTest, cls).setup_credentials()
        cls.os = cls.os_roles_operator
        cls.os_operator = cls.os_roles_operator_alt

    @classmethod
    def resource_setup(cls):
        super(ObjectACLsNegativeTest, cls).resource_setup()
        cls.test_auth_data = cls.os_operator.auth_provider.auth_data

    def setUp(self):
        super(ObjectACLsNegativeTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(ObjectACLsNegativeTest, self).tearDown()

    @test.attr(type=['negative'])
    @test.idempotent_id('af587587-0c24-4e15-9822-8352ce711013')
    def test_write_object_without_using_creds(self):
        # trying to create object with empty headers
        # X-Auth-Token is not provided
        object_name = data_utils.rand_name(name='Object')
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        self.assertRaises(lib_exc.Unauthorized,
                          self.object_client.create_object,
                          self.container_name, object_name, 'data', headers={})

    @test.attr(type=['negative'])
    @test.idempotent_id('af85af0b-a025-4e72-a90e-121babf55720')
    def test_delete_object_without_using_creds(self):
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        # trying to delete object with empty headers
        # X-Auth-Token is not provided
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        self.assertRaises(lib_exc.Unauthorized,
                          self.object_client.delete_object,
                          self.container_name, object_name)

    @test.attr(type=['negative'])
    @test.idempotent_id('63d84e37-55a6-42e2-9e5f-276e60e26a00')
    def test_write_object_with_non_authorized_user(self):
        # attempt to upload another file using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        # trying to create object with non-authorized user
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.create_object,
                          self.container_name, object_name, 'data', headers={})

    @test.attr(type=['negative'])
    @test.idempotent_id('abf63359-be52-4feb-87dd-447689fc77fd')
    def test_read_object_with_non_authorized_user(self):
        # attempt to read object using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(
            self.container_name, object_name, 'data')
        self.assertHeaders(resp, 'Object', 'PUT')
        # trying to get object with non authorized user token
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.get_object,
                          self.container_name, object_name)

    @test.attr(type=['negative'])
    @test.idempotent_id('7343ac3d-cfed-4198-9bb0-00149741a492')
    def test_delete_object_with_non_authorized_user(self):
        # attempt to delete object using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(
            self.container_name, object_name, 'data')
        self.assertHeaders(resp, 'Object', 'PUT')
        # trying to delete object with non-authorized user token
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.delete_object,
                          self.container_name, object_name)

    @test.attr(type=['negative'])
    @test.idempotent_id('9ed01334-01e9-41ea-87ea-e6f465582823')
    def test_read_object_without_rights(self):
        # attempt to read object using non-authorized user
        # update X-Container-Read metadata ACL
        cont_headers = {'X-Container-Read': 'badtenant:baduser'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        self.assertHeaders(resp, 'Object', 'PUT')
        # Trying to read the object without rights
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.get_object,
                          self.container_name, object_name)

    @test.attr(type=['negative'])
    @test.idempotent_id('a3a585a7-d8cf-4b65-a1a0-edc2b1204f85')
    def test_write_object_without_rights(self):
        # attempt to write object using non-authorized user
        # update X-Container-Write metadata ACL
        cont_headers = {'X-Container-Write': 'badtenant:baduser'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # Trying to write the object without rights
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        object_name = data_utils.rand_name(name='Object')
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.create_object,
                          self.container_name,
                          object_name, 'data', headers={})

    @test.attr(type=['negative'])
    @test.idempotent_id('8ba512ad-aa6e-444e-b882-2906a0ea2052')
    def test_write_object_without_write_rights(self):
        # attempt to write object using non-authorized user
        # update X-Container-Read and X-Container-Write metadata ACL
        tenant_name = self.os_operator.credentials.tenant_name
        username = self.os_operator.credentials.username
        cont_headers = {'X-Container-Read':
                        tenant_name + ':' + username,
                        'X-Container-Write': ''}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # Trying to write the object without write rights
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        object_name = data_utils.rand_name(name='Object')
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.create_object,
                          self.container_name,
                          object_name, 'data', headers={})

    @test.attr(type=['negative'])
    @test.idempotent_id('b4e366f8-f185-47ab-b789-df4416f9ecdb')
    def test_delete_object_without_write_rights(self):
        # attempt to delete object using non-authorized user
        # update X-Container-Read and X-Container-Write metadata ACL
        tenant_name = self.os_operator.credentials.tenant_name
        username = self.os_operator.credentials.username
        cont_headers = {'X-Container-Read':
                        tenant_name + ':' + username,
                        'X-Container-Write': ''}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        self.assertHeaders(resp, 'Object', 'PUT')
        # Trying to delete the object without write rights
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(lib_exc.Forbidden,
                          self.object_client.delete_object,
                          self.container_name,
                          object_name)
    
    @test.attr(type=['negative', 'smoke'])
    def test_create_container_with_invalid_container_name_greater_than_255_bytes(self):
        #Container Name greater than 255 bytes
        container_name = data_utils.arbitrary_string(256)
        resp, body = self.container_client.create_container(container_name)
        self.assertNotEqual(resp, '201', 'Container creation successful with invalid container name greater than 255 bytes')

    @test.attr(type=['negative', 'smoke'])
    def test_create_container_with_invalid_container_name_less_than_3_bytes(self): 
        #Container Name less than 3 bytes
        container_name = data_utils.arbitrary_string(2)
        resp, body = self.container_client.create_container(container_name)
        self.assertNotEqual(resp, '201', 'Container creation successful with invalid container name less than 3 bytes')
        
    @test.attr(type=['negative', 'smoke'])
    def test_create_container_with_invalid_container_name_containing_forward_slash(self):    
        #Container Name contains '/'
        container_name = data_utils.arbitrary_string(10)+"/"
        resp, body = self.container_client.create_container(container_name)
        self.assertNotEqual(resp, '201', 'Container creation successful with invalid container name containing /')
        
