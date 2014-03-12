# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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
from tempest import test


class ObjectTestACLs(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ObjectTestACLs, cls).setUpClass()
        cls.data.setup_test_user()
        test_os = clients.Manager(cls.data.test_user,
                                  cls.data.test_password,
                                  cls.data.test_tenant)
        cls.test_auth_data = test_os.auth_provider.auth_data

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(ObjectTestACLs, cls).tearDownClass()

    def setUp(self):
        super(ObjectTestACLs, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(ObjectTestACLs, self).tearDown()

    @test.attr(type='smoke')
    def test_read_object_with_rights(self):
        # attempt to read object using authorized user
        # update X-Container-Read metadata ACL
        cont_headers = {'X-Container-Read':
                        self.data.test_tenant + ':' + self.data.test_user}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, 'data')
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')
        # Trying to read the object with rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        resp, _ = self.custom_object_client.get_object(
            self.container_name, object_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')

    @test.attr(type='smoke')
    def test_write_object_with_rights(self):
        # attempt to write object using authorized user
        # update X-Container-Write metadata ACL
        cont_headers = {'X-Container-Write':
                        self.data.test_tenant + ':' + self.data.test_user}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # Trying to write the object with rights
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.test_auth_data
        )
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.custom_object_client.create_object(
            self.container_name,
            object_name, 'data')
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'PUT')
