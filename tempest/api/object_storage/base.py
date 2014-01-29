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


from tempest.api.identity.base import DataGenerator
from tempest import clients
from tempest.common import custom_matchers
from tempest.common import isolated_creds
from tempest import config
from tempest import exceptions
import tempest.test

CONF = config.CONF


class BaseObjectTest(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(BaseObjectTest, cls).setUpClass()
        if not CONF.service_available.swift:
            skip_msg = ("%s skipped as swift is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.isolated_creds = isolated_creds.IsolatedCreds(
            cls.__name__, network_resources=cls.network_resources)
        if CONF.compute.allow_tenant_isolation:
            # Get isolated creds for normal user
            creds = cls.isolated_creds.get_primary_creds()
            username, tenant_name, password = creds
            cls.os = clients.Manager(username=username,
                                     password=password,
                                     tenant_name=tenant_name)
            # Get isolated creds for admin user
            admin_creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = admin_creds
            cls.os_admin = clients.Manager(username=admin_username,
                                           password=admin_password,
                                           tenant_name=admin_tenant_name)
            # Get isolated creds for alt user
            alt_creds = cls.isolated_creds.get_alt_creds()
            alt_username, alt_tenant, alt_password = alt_creds
            cls.os_alt = clients.Manager(username=alt_username,
                                         password=alt_password,
                                         tenant_name=alt_tenant)
            # Add isolated users to operator role so that they can create a
            # container in swift.
            cls._assign_member_role()
        else:
            cls.os = clients.Manager()
            cls.os_admin = clients.AdminManager()
            cls.os_alt = clients.AltManager()

        cls.object_client = cls.os.object_client
        cls.container_client = cls.os.container_client
        cls.account_client = cls.os.account_client
        cls.custom_object_client = cls.os.custom_object_client
        cls.token_client = cls.os_admin.token_client
        cls.identity_admin_client = cls.os_admin.identity_client
        cls.custom_account_client = cls.os.custom_account_client
        cls.object_client_alt = cls.os_alt.object_client
        cls.container_client_alt = cls.os_alt.container_client
        cls.identity_client_alt = cls.os_alt.identity_client

        cls.data = DataGenerator(cls.identity_admin_client)

    @classmethod
    def tearDownClass(cls):
        cls.isolated_creds.clear_isolated_creds()
        super(BaseObjectTest, cls).tearDownClass()

    @classmethod
    def _assign_member_role(cls):
        primary_user = cls.isolated_creds.get_primary_user()
        alt_user = cls.isolated_creds.get_alt_user()
        swift_role = CONF.object_storage.operator_role
        try:
            resp, roles = cls.os_admin.identity_client.list_roles()
            role = next(r for r in roles if r['name'] == swift_role)
        except StopIteration:
            msg = "No role named %s found" % swift_role
            raise exceptions.NotFound(msg)
        for user in [primary_user, alt_user]:
            cls.os_admin.identity_client.assign_user_role(user['tenantId'],
                                                          user['id'],
                                                          role['id'])

    @classmethod
    def delete_containers(cls, containers, container_client=None,
                          object_client=None):
        """Remove given containers and all objects in them.

        The containers should be visible from the container_client given.
        Will not throw any error if the containers don't exist.
        Will not check that object and container deletions succeed.

        :param containers: list of container names to remove
        :param container_client: if None, use cls.container_client, this means
            that the default testing user will be used (see 'username' in
            'etc/tempest.conf')
        :param object_client: if None, use cls.object_client
        """
        if container_client is None:
            container_client = cls.container_client
        if object_client is None:
            object_client = cls.object_client
        for cont in containers:
            try:
                objlist = container_client.list_all_container_objects(cont)
                # delete every object in the container
                for obj in objlist:
                    object_client.delete_object(cont, obj['name'])
                container_client.delete_container(cont)
            except exceptions.NotFound:
                pass

    def assertHeaders(self, resp, target, method):
        """
        Common method to check the existence and the format of common response
        headers
        """
        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        target, method))
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
