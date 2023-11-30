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

from oslo_log import log

from tempest.common import custom_matchers
from tempest.common import object_storage
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF
LOG = log.getLogger(__name__)


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

    @classmethod
    def setup_clients(cls):
        super(BaseObjectTest, cls).setup_clients()
        cls.object_client = cls.os_roles_operator.object_client
        cls.bulk_client = cls.os_roles_operator.bulk_client
        cls.container_client = cls.os_roles_operator.container_client
        cls.account_client = cls.os_roles_operator.account_client
        cls.capabilities_client = cls.os_roles_operator.capabilities_client

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
            body = cls.capabilities_client.list_capabilities()

            if 'swift' in body and 'policies' in body['swift']:
                cls.policies = body['swift']['policies']

        cls.containers = []

    @classmethod
    def create_container(cls):
        # wrapper that returns a test container
        container_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='TestContainer')
        cls.container_client.update_container(container_name)
        cls.containers.append(container_name)

        return container_name

    @classmethod
    def create_object(cls, container_name, object_name=None,
                      data=None, metadata=None):
        # wrapper that returns a test object
        if object_name is None:
            object_name = data_utils.rand_name(
                prefix=CONF.resource_name_prefix, name='TestObject')
        if data is None:
            data = data_utils.random_bytes()

        err = Exception()
        for _ in range(5):
            try:
                cls.object_client.create_object(container_name,
                                                object_name,
                                                data,
                                                metadata=metadata)
                waiters.wait_for_object_create(cls.object_client,
                                               container_name,
                                               object_name)
                return object_name, data
            # after bucket creation we might see Conflict
            except lib_exc.Conflict as e:
                err = e
                time.sleep(2)
        raise err

    @classmethod
    def delete_containers(cls, container_client=None, object_client=None):
        if container_client is None:
            container_client = cls.container_client
        if object_client is None:
            object_client = cls.object_client
        object_storage.delete_containers(cls.containers, container_client,
                                         object_client)

    def assertHeaders(self, resp, target, method):
        """Check the existence and the format of response headers"""

        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        target, method, self.policies))
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
