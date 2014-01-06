# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
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
from tempest import clients
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class ObjectACLsNegativeTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ObjectACLsNegativeTest, cls).setUpClass()
        cls.data.setup_test_user()
        test_os = clients.Manager(cls.data.test_user,
                                  cls.data.test_password,
                                  cls.data.test_tenant)
        cls.test_auth_data = test_os.get_auth_provider().auth_data

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(ObjectACLsNegativeTest, cls).tearDownClass()

    def setUp(self):
        super(ObjectACLsNegativeTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(ObjectACLsNegativeTest, self).tearDown()

    @attr(type=['negative', 'gate'])
    def test_write_object_without_using_creds(self):
        # trying to create object with empty headers
        # X-Auth-Token is not provided
        object_name = data_utils.rand_name(name='Object')
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name, object_name, 'data')

    @attr(type=['negative', 'gate'])
    def test_delete_object_without_using_creds(self):
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        # trying to delete object with empty headers
        # X-Auth-Token is not provided
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.delete_object,
                          self.container_name, object_name)

    @attr(type=['negative', 'gate'])
    def test_write_object_with_non_authorized_user(self):
        # attempt to upload another file using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        # trying to create object with non-authorized user
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name, object_name, 'data')

    @attr(type=['negative', 'gate'])
    def test_read_object_with_non_authorized_user(self):
        # attempt to read object using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(
            self.container_name, object_name, 'data')
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')
        # trying to get object with non authorized user token
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.get_object,
                          self.container_name, object_name)

    @attr(type=['negative', 'gate'])
    def test_delete_object_with_non_authorized_user(self):
        # attempt to delete object using non-authorized user
        # User provided token is forbidden. ACL are not set
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(
            self.container_name, object_name, 'data')
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')
        # trying to delete object with non-authorized user token
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.delete_object,
                          self.container_name, object_name)

    @attr(type=['negative', 'smoke'])
    def test_read_object_without_rights(self):
        # attempt to read object using non-authorized user
        # update X-Container-Read metadata ACL
        cont_headers = {'X-Container-Read': 'badtenant:baduser'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')
        # Trying to read the object without rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.get_object,
                          self.container_name, object_name)

    @attr(type=['negative', 'smoke'])
    def test_write_object_without_rights(self):
        # attempt to write object using non-authorized user
        # update X-Container-Write metadata ACL
        cont_headers = {'X-Container-Write': 'badtenant:baduser'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # Trying to write the object without rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        object_name = data_utils.rand_name(name='Object')
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name,
                          object_name, 'data')

    @attr(type=['negative', 'smoke'])
    def test_write_object_without_write_rights(self):
        # attempt to write object using non-authorized user
        # update X-Container-Read and X-Container-Write metadata ACL
        cont_headers = {'X-Container-Read':
                        self.data.test_tenant + ':' + self.data.test_user,
                        'X-Container-Write': ''}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # Trying to write the object without write rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        object_name = data_utils.rand_name(name='Object')
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name,
                          object_name, 'data')

    @attr(type=['negative', 'smoke'])
    def test_delete_object_without_write_rights(self):
        # attempt to delete object using non-authorized user
        # update X-Container-Read and X-Container-Write metadata ACL
        cont_headers = {'X-Container-Read':
                        self.data.test_tenant + ':' + self.data.test_user,
                        'X-Container-Write': ''}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')
        # Trying to delete the object without write rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.delete_object,
                          self.container_name,
                          object_name)
