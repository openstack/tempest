# Copyright 2017 IBM Corp.
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

import mock

from tempest.tests import base


class ConfCounter(object):

    def __init__(self, *args, **kwargs):
        self.count = 0

    def __getattr__(self, key):
        self.count += 1
        return mock.MagicMock()

    def get_counts(self):
        return self.count


class TestImports(base.TestCase):
    def setUp(self):
        super(TestImports, self).setUp()
        self.conf_mock = self.patch('tempest.config.CONF',
                                    new_callable=ConfCounter)

    def test_account_generator_command_import(self):
        from tempest.cmd import account_generator  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_cleanup_command_import(self):
        from tempest.cmd import cleanup  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_init_command_import(self):
        from tempest.cmd import init  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_list_plugins_command_import(self):
        from tempest.cmd import list_plugins  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_run_command_import(self):
        from tempest.cmd import run  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_subunit_descibe_command_import(self):
        from tempest.cmd import subunit_describe_calls  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_verify_tempest_config_command_import(self):
        from tempest.cmd import verify_tempest_config  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())

    def test_workspace_command_import(self):
        from tempest.cmd import workspace  # noqa
        self.assertEqual(0, self.conf_mock.get_counts())
