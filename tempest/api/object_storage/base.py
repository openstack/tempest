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

from tempest_lib import exceptions as lib_exc

from tempest import clients
from tempest.common import credentials
from tempest.common import custom_matchers
from tempest import config
import tempest.test

CONF = config.CONF


class BaseObjectTest(tempest.test.BaseTestCase):

    @classmethod
    def skip_checks(cls):
        super(BaseObjectTest, cls).skip_checks()
        if not CONF.service_available.swift:
            skip_msg = ("%s skipped as swift is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseObjectTest, cls).setup_credentials()
        cls.isolated_creds = credentials.get_isolated_credentials(
            cls.__name__, network_resources=cls.network_resources)
        operator_role = CONF.object_storage.operator_role
        if not cls.isolated_creds.is_role_available(operator_role):
            skip_msg = ("%s skipped because the configured credential provider"
                        " is not able to provide credentials with the %s role "
                        "assigned." % (cls.__name__, operator_role))
            raise cls.skipException(skip_msg)
        else:
            # Get isolated creds for normal user
            cls.os = clients.Manager(cls.isolated_creds.get_creds_by_roles(
                [operator_role]))

    @classmethod
    def setup_clients(cls):
        super(BaseObjectTest, cls).setup_clients()
        cls.object_client = cls.os.object_client
        cls.container_client = cls.os.container_client
        cls.account_client = cls.os.account_client

    @classmethod
    def resource_setup(cls):
        super(BaseObjectTest, cls).resource_setup()

        # Make sure we get fresh auth data after assigning swift role
        cls.object_client.auth_provider.clear_auth()
        cls.container_client.auth_provider.clear_auth()
        cls.account_client.auth_provider.clear_auth()

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
                    try:
                        object_client.delete_object(cont, obj['name'])
                    except lib_exc.NotFound:
                        pass
                container_client.delete_container(cont)
            except lib_exc.NotFound:
                pass

    def assertHeaders(self, resp, target, method):
        """
        Common method to check the existence and the format of common response
        headers
        """
        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        target, method))
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
