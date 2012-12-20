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

import logging
import time

import nose
import unittest2 as unittest

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest import exceptions

LOG = logging.getLogger(__name__)


class BaseVolumeTest(unittest.TestCase):

    """Base test case class for all Cinder API tests"""

    @classmethod
    def setUpClass(cls):
        cls.config = config.TempestConfig()
        cls.isolated_creds = []

        if cls.config.compute.allow_tenant_isolation:
            creds = cls._get_isolated_creds()
            username, tenant_name, password = creds
            os = clients.Manager(username=username,
                                 password=password,
                                 tenant_name=tenant_name)
        else:
            os = clients.Manager()

        cls.os = os
        cls.volumes_client = os.volumes_client
        cls.servers_client = os.servers_client
        cls.image_ref = cls.config.compute.image_ref
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.build_interval = cls.config.volume.build_interval
        cls.build_timeout = cls.config.volume.build_timeout
        cls.volumes = {}

        skip_msg = ("%s skipped as Cinder endpoint is not available" %
                    cls.__name__)
        try:
            cls.volumes_client.keystone_auth(cls.os.username,
                                             cls.os.password,
                                             cls.os.auth_url,
                                             cls.volumes_client.service,
                                             cls.os.tenant_name)
        except exceptions.EndpointNotFound:
            cls.clear_isolated_creds()
            raise nose.SkipTest(skip_msg)

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = clients.IdentityManager()
        return os.admin_client

    @classmethod
    def _get_isolated_creds(cls):
        """
        Creates a new set of user/tenant/password credentials for a
        **regular** user of the Volume API so that a test case can
        operate in an isolated tenant container.
        """
        admin_client = cls._get_identity_admin_client()
        rand_name_root = cls.__name__
        if cls.isolated_creds:
            # Main user already created. Create the alt one...
            rand_name_root += '-alt'
        username = rand_name_root + "-user"
        email = rand_name_root + "@example.com"
        tenant_name = rand_name_root + "-tenant"
        tenant_desc = tenant_name + "-desc"
        password = "pass"

        resp, tenant = admin_client.create_tenant(name=tenant_name,
                                                  description=tenant_desc)
        resp, user = admin_client.create_user(username,
                                              password,
                                              tenant['id'],
                                              email)
        # Store the complete creds (including UUID ids...) for later
        # but return just the username, tenant_name, password tuple
        # that the various clients will use.
        cls.isolated_creds.append((user, tenant))

        return username, tenant_name, password

    @classmethod
    def clear_isolated_creds(cls):
        if not cls.isolated_creds:
            pass
        admin_client = cls._get_identity_admin_client()

        for user, tenant in cls.isolated_creds:
            admin_client.delete_user(user['id'])
            admin_client.delete_tenant(tenant['id'])

    @classmethod
    def tearDownClass(cls):
        cls.clear_isolated_creds()

    def create_volume(self, size=1, metadata={}):
        """Wrapper utility that returns a test volume"""
        display_name = rand_name(self.__class__.__name__ + "-volume")
        cli_resp = self.volumes_client.create_volume(size=size,
                                                     display_name=display_name,
                                                     metdata=metadata)
        resp, volume = cli_resp
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.volumes.append(volume)
        return volume

    def wait_for(self, condition):
        """Repeatedly calls condition() until a timeout"""
        start_time = int(time.time())
        while True:
            try:
                condition()
            except Exception:
                pass
            else:
                return
            if int(time.time()) - start_time >= self.build_timeout:
                condition()
                return
            time.sleep(self.build_interval)


class BaseVolumeTestJSON(BaseVolumeTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(BaseVolumeTestJSON, cls).setUpClass()


class BaseVolumeTestXML(BaseVolumeTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(BaseVolumeTestXML, cls).setUpClass()
