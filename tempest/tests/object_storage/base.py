# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import nose
import unittest2 as unittest

from tempest import clients
import tempest.config
from tempest import exceptions
from tempest.tests.identity.base import DataGenerator


class BaseObjectTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = clients.Manager()
        cls.object_client = cls.os.object_client
        cls.container_client = cls.os.container_client
        cls.account_client = cls.os.account_client
        cls.config = cls.os.config
        cls.custom_object_client = cls.os.custom_object_client
        cls.os_admin = clients.AdminManager()
        cls.token_client = cls.os_admin.token_client
        cls.identity_admin_client = cls.os_admin.identity_client
        cls.custom_account_client = cls.os.custom_account_client
        cls.os_alt = clients.AltManager()
        cls.object_client_alt = cls.os_alt.object_client
        cls.container_client_alt = cls.os_alt.container_client
        cls.identity_client_alt = cls.os_alt.identity_client

        cls.data = DataGenerator(cls.identity_admin_client)

        try:
            cls.account_client.list_account_containers()
        except exceptions.EndpointNotFound:
            enabled = False
            skip_msg = "No OpenStack Object Storage API endpoint"
            raise nose.SkipTest(skip_msg)
