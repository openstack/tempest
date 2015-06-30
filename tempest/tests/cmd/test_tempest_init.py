# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import fixtures

from tempest.cmd import init
from tempest.tests import base


class TestTempestInit(base.TestCase):

    def test_generate_testr_conf(self):
        # Create fake conf dir
        conf_dir = self.useFixture(fixtures.TempDir())

        init_cmd = init.TempestInit(None, None)
        init_cmd.generate_testr_conf(conf_dir.path)

        # Generate expected file contents
        top_level_path = os.path.dirname(os.path.dirname(init.__file__))
        discover_path = os.path.join(top_level_path, 'test_discover')
        testr_conf_file = init.TESTR_CONF % (top_level_path, discover_path)

        conf_path = conf_dir.join('.testr.conf')
        conf_file = open(conf_path, 'r')
        self.addCleanup(conf_file.close)
        self.assertEqual(conf_file.read(), testr_conf_file)

    def test_create_working_dir(self):
        fake_local_dir = self.useFixture(fixtures.TempDir())
        fake_local_conf_dir = self.useFixture(fixtures.TempDir())
        # Create a fake conf file
        fake_file = fake_local_conf_dir.join('conf_file.conf')
        open(fake_file, 'w').close()
        init_cmd = init.TempestInit(None, None)
        init_cmd.create_working_dir(fake_local_dir.path,
                                    fake_local_conf_dir.path)
        # Assert directories are created
        lock_path = os.path.join(fake_local_dir.path, 'tempest_lock')
        etc_dir = os.path.join(fake_local_dir.path, 'etc')
        log_dir = os.path.join(fake_local_dir.path, 'logs')
        testr_dir = os.path.join(fake_local_dir.path, '.testrepository')
        self.assertTrue(os.path.isdir(lock_path))
        self.assertTrue(os.path.isdir(etc_dir))
        self.assertTrue(os.path.isdir(log_dir))
        self.assertTrue(os.path.isdir(testr_dir))
        # Assert file creation
        fake_file_moved = os.path.join(etc_dir, 'conf_file.conf')
        local_conf_file = os.path.join(etc_dir, 'tempest.conf')
        local_testr_conf = os.path.join(fake_local_dir.path, '.testr.conf')
        self.assertTrue(os.path.isfile(fake_file_moved))
        self.assertTrue(os.path.isfile(local_conf_file))
        self.assertTrue(os.path.isfile(local_testr_conf))
