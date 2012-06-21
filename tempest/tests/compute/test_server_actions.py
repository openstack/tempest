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

import base64
import time

from nose.plugins.attrib import attr
import unittest2 as unittest

import tempest.config
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.compute.base import BaseComputeTest


class ServerActionsTest(BaseComputeTest):

    resize_available = tempest.config.TempestConfig().compute.resize_available

    @classmethod
    def setUpClass(cls):
        super(ServerActionsTest, cls).setUpClass()
        cls.client = cls.servers_client

    def setUp(self):
        self.name = rand_name('server')
        resp, server = self.client.create_server(self.name,
                                                 self.image_ref,
                                                 self.flavor_ref)
        self.server_id = server['id']

        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        self.client.delete_server(self.server_id)

    @attr(type='smoke')
    def test_change_server_password(self):
        """The server's password should be set to the provided password"""
        resp, body = self.client.change_password(self.server_id, 'newpass')
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='smoke')
    def test_reboot_server_hard(self):
        """ The server should be power cycled """
        resp, body = self.client.reboot(self.server_id, 'HARD')
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='smoke')
    @unittest.skip('Until bug 1014647 is dealt with.')
    def test_reboot_server_soft(self):
        """The server should be signaled to reboot gracefully"""
        resp, body = self.client.reboot(self.server_id, 'SOFT')
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='smoke')
    def test_rebuild_server(self):
        """ The server should be rebuilt using the provided image and data """
        meta = {'rebuild': 'server'}
        new_name = rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': '/etc/rebuild.txt',
                       'contents': base64.b64encode(file_contents)}]

        resp, rebuilt_server = self.client.rebuild(self.server_id,
                                                   self.image_ref_alt,
                                                   name=new_name, meta=meta,
                                                   personality=personality,
                                                   adminPass='rebuild')

        #Verify the properties in the initial response are correct
        self.assertEqual(self.server_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(self.flavor_ref, rebuilt_server['flavor']['id'])

        #Verify the server properties after the rebuild completes
        self.client.wait_for_server_status(rebuilt_server['id'], 'ACTIVE')
        resp, server = self.client.get_server(rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertTrue(self.image_ref_alt.endswith(rebuilt_image_id))
        self.assertEqual(new_name, rebuilt_server['name'])

    @attr(type='smoke')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_confirm(self):
        """
        The server's RAM and disk space should be modified to that of
        the provided flavor
        """

        resp, server = self.client.resize(self.server_id, self.flavor_ref_alt)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.confirm_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        resp, server = self.client.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavor']['id'])

    @attr(type='smoke')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_revert(self):
        """
        The server's RAM and disk space should return to its original
        values after a resize is reverted
        """

        resp, server = self.client.resize(self.server_id, self.flavor_ref_alt)
        self.assertEqual(202, resp.status)
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        self.client.revert_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        # Need to poll for the id change until lp#924371 is fixed
        resp, server = self.client.get_server(self.server_id)
        start = int(time.time())

        while server['flavor']['id'] != self.flavor_ref:
            time.sleep(self.build_interval)
            resp, server = self.client.get_server(self.server_id)

            if int(time.time()) - start >= self.build_timeout:
                message = 'Server %s failed to revert resize within the \
                required time (%s s).' % (self.server_id, self.build_timeout)
                raise exceptions.TimeoutException(message)

    @attr(type='negative')
    def test_reboot_nonexistant_server_soft(self):
        """
        Negative Test: The server reboot on non existant server should return
        an error
        """
        self.assertRaises(exceptions.NotFound, self.client.reboot, 999, 'SOFT')

    @unittest.skip('Until bug 963248 is fixed.')
    @attr(type='negative')
    def test_rebuild_nonexistant_server(self):
        """
        Negative test: The server rebuild for a non existing server should not
        be allowed
        """
        meta = {'rebuild': 'server'}
        new_name = rand_name('server')
        file_contents = 'Test server rebuild.'
        personality = [{'path': '/etc/rebuild.txt',
                        'contents': base64.b64encode(file_contents)}]
        try:
            resp, rebuilt_server = self.client.rebuild(999,
                                       self.image_ref_alt, name=new_name,
                                       meta=meta, personality=personality,
                                       adminPass='rebuild')
        except exceptions.NotFound:
            pass
        else:
            self.fail('The server rebuild for a non existing server should not'
                      ' be allowed')
