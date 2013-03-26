# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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
import subprocess

import testtools

import cli


LOG = logging.getLogger(__name__)


class SimpleReadOnlyNovaManageTest(cli.ClientTestBase):

    """
    This is a first pass at a simple read only nova-manage test. This
    only exercises client commands that are read only.

    This should test commands:
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """

    def test_admin_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.nova_manage,
                          'this-does-nova-exist')

    #NOTE(jogo): Commands in order listed in 'nova-manage -h'

    # test flags
    def test_help_flag(self):
        self.nova_manage('', '-h')

    def test_version_flag(self):
        # Bug 1159957: nova-manage --version writes to stderr
        self.assertNotEqual("", self.nova_manage('', '--version',
                                                 merge_stderr=True))
        self.assertEqual(self.nova_manage('version'),
                         self.nova_manage('', '--version', merge_stderr=True))

    def test_debug_flag(self):
        self.assertNotEqual("", self.nova_manage('instance_type list',
                            '--debug'))

    def test_verbose_flag(self):
        self.assertNotEqual("", self.nova_manage('instance_type list',
                            '--verbose'))

    # test actions
    def test_version(self):
        self.assertNotEqual("", self.nova_manage('version'))

    def test_flavor_list(self):
        self.assertNotEqual("", self.nova_manage('flavor list'))
        self.assertEqual(self.nova_manage('instance_type list'),
                         self.nova_manage('flavor list'))

    def test_db_archive_deleted_rows(self):
        # make sure command doesn't error out
        self.nova_manage('db archive_deleted_rows 50')

    def test_db_sync(self):
        # make sure command doesn't error out
        self.nova_manage('db sync')

    def test_db_version(self):
        self.assertNotEqual("", self.nova_manage('db version'))
