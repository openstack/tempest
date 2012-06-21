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
from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.compute.base import BaseComputeTest
from tempest.tests import compute


class TestServerDiskConfig(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        if not compute.DISK_CONFIG_ENABLED:
            msg = "DiskConfig extension not enabled."
            raise nose.SkipTest(msg)
        super(TestServerDiskConfig, cls).setUpClass()
        cls.client = cls.os.servers_client

    @attr(type='positive')
    def test_create_server_with_manual_disk_config(self):
        """A server should be created with manual disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    def test_create_server_with_auto_disk_config(self):
        """A server should be created with auto disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    def test_rebuild_server_with_manual_disk_config(self):
        """A server should be rebuilt using the manual disk config option"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        resp, server = self.client.rebuild(server['id'],
                                           self.image_ref_alt,
                                           disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    def test_rebuild_server_with_auto_disk_config(self):
        """A server should be rebuilt using the auto disk config option"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        resp, server = self.client.rebuild(server['id'],
                                           self.image_ref_alt,
                                           disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @unittest.skipUnless(compute.RESIZE_AVAILABLE, 'Resize not available.')
    def test_resize_server_from_manual_to_auto(self):
        """A server should be resized from manual to auto disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Resize with auto option
        self.client.resize(server['id'], self.flavor_ref_alt,
                           disk_config='AUTO')
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.confirm_resize(server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @unittest.skipUnless(compute.RESIZE_AVAILABLE, 'Resize not available.')
    def test_resize_server_from_auto_to_manual(self):
        """A server should be resized from auto to manual disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Resize with manual option
        self.client.resize(server['id'], self.flavor_ref_alt,
                           disk_config='MANUAL')
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.confirm_resize(server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])
