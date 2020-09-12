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

    def test_generate_stestr_conf(self):
        # Create fake conf dir
        conf_dir = self.useFixture(fixtures.TempDir())

        init_cmd = init.TempestInit(None, None)
        init_cmd.generate_stestr_conf(conf_dir.path)

        # Generate expected file contents
        top_level_path = os.path.dirname(os.path.dirname(init.__file__))
        discover_path = os.path.join(top_level_path, 'test_discover')
        stestr_conf_file = init.STESTR_CONF % (discover_path, top_level_path)

        conf_path = conf_dir.join('.stestr.conf')
        with open(conf_path, 'r') as conf_file:
            self.assertEqual(conf_file.read(), stestr_conf_file)

    def test_generate_sample_config(self):
        local_dir = self.useFixture(fixtures.TempDir())
        etc_dir_path = os.path.join(local_dir.path, 'etc')
        os.mkdir(etc_dir_path)
        init_cmd = init.TempestInit(None, None)
        local_sample_conf_file = os.path.join(etc_dir_path,
                                              'tempest.conf.sample')

        # Verify no sample config file exist
        self.assertFalse(os.path.isfile(local_sample_conf_file))
        init_cmd.generate_sample_config(local_dir.path)

        # Verify sample config file exist with some content
        self.assertTrue(os.path.isfile(local_sample_conf_file))
        self.assertGreater(os.path.getsize(local_sample_conf_file), 0)

    def test_update_local_conf(self):
        local_dir = self.useFixture(fixtures.TempDir())
        etc_dir_path = os.path.join(local_dir.path, 'etc')
        os.mkdir(etc_dir_path)
        lock_dir = os.path.join(local_dir.path, 'tempest_lock')
        config_path = os.path.join(etc_dir_path, 'tempest.conf')
        log_dir = os.path.join(local_dir.path, 'logs')

        init_cmd = init.TempestInit(None, None)

        # Generate the config file
        init_cmd.generate_sample_config(local_dir.path)

        # Create a conf file with populated values
        config_parser_pre = init_cmd.get_configparser(config_path)
        with open(config_path, 'w+') as conf_file:
            # create the same section init will check for and add values to
            config_parser_pre.add_section('oslo_concurrency')
            config_parser_pre.set('oslo_concurrency', 'TEST', local_dir.path)
            # create a new section
            config_parser_pre.add_section('TEST')
            config_parser_pre.set('TEST', 'foo', "bar")
            config_parser_pre.write(conf_file)

        # Update the config file the same way tempest init does
        init_cmd.update_local_conf(config_path, lock_dir, log_dir)

        # parse the new config file to verify it
        config_parser_post = init_cmd.get_configparser(config_path)

        # check that our value in oslo_concurrency wasn't overwritten
        self.assertTrue(config_parser_post.has_section('oslo_concurrency'))
        self.assertEqual(config_parser_post.get('oslo_concurrency', 'TEST'),
                         local_dir.path)
        # check that the lock directory was set correctly
        self.assertEqual(config_parser_post.get('oslo_concurrency',
                                                'lock_path'), lock_dir)

        # check that our new section still exists and wasn't modified
        self.assertTrue(config_parser_post.has_section('TEST'))
        self.assertEqual(config_parser_post.get('TEST', 'foo'), 'bar')

        # check that the DEFAULT values are correct
        # NOTE(auggy): has_section ignores DEFAULT
        self.assertEqual(config_parser_post.get('DEFAULT', 'log_dir'), log_dir)

    def test_create_working_dir_with_existing_local_dir_non_empty(self):
        fake_local_dir = self.useFixture(fixtures.TempDir())
        fake_local_conf_dir = self.useFixture(fixtures.TempDir())
        open("%s/foo" % fake_local_dir.path, 'w').close()

        _init = init.TempestInit(None, None)
        self.assertRaises(OSError,
                          _init.create_working_dir,
                          fake_local_dir.path,
                          fake_local_conf_dir.path)

    def test_create_working_dir(self):
        fake_local_dir = self.useFixture(fixtures.TempDir())
        fake_local_conf_dir = self.useFixture(fixtures.TempDir())
        os.rmdir(fake_local_dir.path)
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
        stestr_dir = os.path.join(fake_local_dir.path, '.stestr')
        self.assertTrue(os.path.isdir(lock_path))
        self.assertTrue(os.path.isdir(etc_dir))
        self.assertTrue(os.path.isdir(log_dir))
        self.assertTrue(os.path.isdir(stestr_dir))
        # Assert file creation
        fake_file_moved = os.path.join(etc_dir, 'conf_file.conf')
        local_conf_file = os.path.join(etc_dir, 'tempest.conf')
        local_stestr_conf = os.path.join(fake_local_dir.path, '.stestr.conf')
        self.assertTrue(os.path.isfile(fake_file_moved))
        self.assertTrue(os.path.isfile(local_conf_file))
        self.assertTrue(os.path.isfile(local_stestr_conf))

    def test_take_action_fails(self):
        class ParsedArgs(object):
            workspace_dir = self.useFixture(fixtures.TempDir()).path
            workspace_path = os.path.join(workspace_dir, 'workspace.yaml')
            name = 'test'
            dir_base = self.useFixture(fixtures.TempDir()).path
            dir = os.path.join(dir_base, 'foo', 'bar')
            config_dir = self.useFixture(fixtures.TempDir()).path
            show_global_dir = False
        pa = ParsedArgs()
        init_cmd = init.TempestInit(None, None)
        self.assertRaises(OSError, init_cmd.take_action, pa)
        # one more trying should be a same error not "workspace already exists"
        self.assertRaises(OSError, init_cmd.take_action, pa)
