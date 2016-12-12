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

import time

from tempest.common import custom_matchers
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF


class BaseObjectTest(tempest.test.BaseTestCase):

    credentials = [['operator', CONF.object_storage.operator_role]]

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
        # credentials may be overwritten by children classes
        if hasattr(cls, 'os_roles_operator'):
            cls.os = cls.os_roles_operator

    @classmethod
    def setup_clients(cls):
        super(BaseObjectTest, cls).setup_clients()
        cls.object_client = cls.os.object_client
        cls.container_client = cls.os.container_client
        cls.account_client = cls.os.account_client
        cls.capabilities_client = cls.os.capabilities_client

    @classmethod
    def resource_setup(cls):
        super(BaseObjectTest, cls).resource_setup()

        # Make sure we get fresh auth data after assigning swift role
        cls.object_client.auth_provider.clear_auth()
        cls.container_client.auth_provider.clear_auth()
        cls.account_client.auth_provider.clear_auth()

        # make sure that discoverability is enabled and that the sections
        # have not been disallowed by Swift
        cls.policies = None

        if CONF.object_storage_feature_enabled.discoverability:
            _, body = cls.capabilities_client.list_capabilities()

            if 'swift' in body and 'policies' in body['swift']:
                cls.policies = body['swift']['policies']

        cls.containers = []

    @classmethod
    def create_container(cls):
        # wrapper that returns a test container
        container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(container_name)
        cls.containers.append(container_name)

        return container_name

    @classmethod
    def create_object(cls, container_name, object_name=None,
                      data=None, metadata=None):
        # wrapper that returns a test object
        if object_name is None:
            object_name = data_utils.rand_name(name='TestObject')
        if data is None:
            data = data_utils.arbitrary_string()
        cls.object_client.create_object(container_name,
                                        object_name,
                                        data,
                                        metadata=metadata)

        return object_name, data

    @classmethod
    def delete_containers(cls, container_client=None,
                          object_client=None):
        """Remove containers and all objects in them.

        The containers should be visible from the container_client given.
        Will not throw any error if the containers don't exist.
        Will not check that object and container deletions succeed.
        After delete all the objects from a container, it will wait 2
        seconds before delete the container itself, in order to deployments
        using HA proxy sync the deletion properly, otherwise, the container
        might fail to be deleted because it's not empty.

        :param container_client: if None, use cls.container_client, this means
            that the default testing user will be used (see 'username' in
            'etc/tempest.conf')
        :param object_client: if None, use cls.object_client
        """
        if container_client is None:
            container_client = cls.container_client
        if object_client is None:
            object_client = cls.object_client
        for cont in cls.containers:
            try:
                params = {'limit': 9999, 'format': 'json'}
                resp, objlist = container_client.list_container_contents(
                    cont, params)
                # delete every object in the container
                for obj in objlist:
                    test_utils.call_and_ignore_notfound_exc(
                        object_client.delete_object, cont, obj['name'])
                # sleep 2 seconds to sync the deletion of the objects
                # in HA deployment
                time.sleep(2)
                container_client.delete_container(cont)
            except lib_exc.NotFound:
                pass

    def assertHeaders(self, resp, target, method):
        """Check the existence and the format of response headers"""

        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        target, method, self.policies))
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
