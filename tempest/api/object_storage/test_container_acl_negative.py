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

from tempest.api.object_storage import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ObjectACLsNegativeTest(base.BaseObjectTest):
    """Negative tests of object ACLs"""

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['operator_alt', CONF.object_storage.operator_role]]

    @classmethod
    def setup_credentials(cls):
        super(ObjectACLsNegativeTest, cls).setup_credentials()
        cls.os_operator = cls.os_roles_operator_alt

    @classmethod
    def resource_setup(cls):
        super(ObjectACLsNegativeTest, cls).resource_setup()
        cls.test_auth_data = cls.os_operator.auth_provider.auth_data

    def setUp(self):
        super(ObjectACLsNegativeTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.update_container(self.container_name)

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers()
        super(ObjectACLsNegativeTest, cls).resource_cleanup()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('af587587-0c24-4e15-9822-8352ce711013')
    def test_write_object_without_using_creds(self):
        """Test writing object without using credentials"""
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('af85af0b-a025-4e72-a90e-121babf55720')
    def test_delete_object_without_using_creds(self):
        """Test deleting object without using credentials"""
        # create object
        object_name = data_utils.rand_name(name='Object')
        self.object_client.create_object(self.container_name, object_name,
                                         'data')
        # trying to delete object with empty headers
        # X-Auth-Token is not provided
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        self.assertRaises(lib_exc.Unauthorized,
                          self.object_client.delete_object,
                          self.container_name, object_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('63d84e37-55a6-42e2-9e5f-276e60e26a00')
    def test_write_object_with_non_authorized_user(self):
        """Test writing object with non-authorized user"""
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('abf63359-be52-4feb-87dd-447689fc77fd')
    def test_read_object_with_non_authorized_user(self):
        """Test reading object with non-authorized user"""
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7343ac3d-cfed-4198-9bb0-00149741a492')
    def test_delete_object_with_non_authorized_user(self):
        """Test deleting object with non-authorized user"""
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9ed01334-01e9-41ea-87ea-e6f465582823')
    def test_read_object_without_rights(self):
        """Test reading object without rights"""
        # update X-Container-Read metadata ACL
        cont_headers = {'X-Container-Read': 'badtenant:baduser'}
        resp_meta, _ = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a3a585a7-d8cf-4b65-a1a0-edc2b1204f85')
    def test_write_object_without_rights(self):
        """Test writing object without rights"""
        # update X-Container-Write metadata ACL
        cont_headers = {'X-Container-Write': 'badtenant:baduser'}
        resp_meta, _ = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8ba512ad-aa6e-444e-b882-2906a0ea2052')
    def test_write_object_without_write_rights(self):
        """Test writing object without write rights"""
        # update X-Container-Read and X-Container-Write metadata ACL
        tenant_name = self.os_operator.credentials.tenant_name
        username = self.os_operator.credentials.username
        cont_headers = {'X-Container-Read':
                        tenant_name + ':' + username,
                        'X-Container-Write': ''}
        resp_meta, _ = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b4e366f8-f185-47ab-b789-df4416f9ecdb')
    def test_delete_object_without_write_rights(self):
        """Test deleting object without write rights"""
        # update X-Container-Read and X-Container-Write metadata ACL
        tenant_name = self.os_operator.credentials.tenant_name
        username = self.os_operator.credentials.username
        cont_headers = {'X-Container-Read':
                        tenant_name + ':' + username,
                        'X-Container-Write': ''}
        resp_meta, _ = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
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
