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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ObjectTestACLs(base.BaseObjectTest):

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['operator_alt', CONF.object_storage.operator_role]]

    def setUp(self):
        super(ObjectTestACLs, self).setUp()
        self.container_name = self.create_container()

    def tearDown(self):
        self.delete_containers()
        super(ObjectTestACLs, self).tearDown()

    @decorators.idempotent_id('a3270f3f-7640-4944-8448-c7ea783ea5b6')
    def test_read_object_with_rights(self):
        # attempt to read object using authorized user
        # update X-Container-Read metadata ACL
        tenant_id = self.os_roles_operator_alt.credentials.tenant_id
        user_id = self.os_roles_operator_alt.credentials.user_id
        cont_headers = {'X-Container-Read': tenant_id + ':' + user_id}
        container_client = self.os_roles_operator.container_client
        resp_meta, _ = (
            container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # create object
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.os_roles_operator.object_client.create_object(
            self.container_name, object_name, 'data')
        self.assertHeaders(resp, 'Object', 'PUT')
        # set alternative authentication data; cannot simply use the
        # other object client.
        self.os_roles_operator.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.os_roles_operator_alt.object_client.auth_provider.
            auth_data)
        resp, _ = self.os_roles_operator.object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

    @decorators.idempotent_id('aa58bfa5-40d9-4bc3-82b4-d07f4a9e392a')
    def test_write_object_with_rights(self):
        # attempt to write object using authorized user
        # update X-Container-Write metadata ACL
        tenant_id = self.os_roles_operator_alt.credentials.tenant_id
        user_id = self.os_roles_operator_alt.credentials.user_id
        cont_headers = {'X-Container-Write': tenant_id + ':' + user_id}
        container_client = self.os_roles_operator.container_client
        resp_meta, _ = (
            container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
        self.assertHeaders(resp_meta, 'Container', 'POST')
        # set alternative authentication data; cannot simply use the
        # other object client.
        self.os_roles_operator.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.os_roles_operator_alt.object_client.auth_provider.
            auth_data)
        # Trying to write the object with rights
        object_name = data_utils.rand_name(name='Object')
        resp, _ = self.os_roles_operator.object_client.create_object(
            self.container_name,
            object_name, 'data', headers={})
        self.assertHeaders(resp, 'Object', 'PUT')
