# Copyright 2014 IBM Corp.
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

import mock
from tempest_lib.cli import base as cli_base
import testtools

from tempest import cli
from tempest import config
from tempest import exceptions
from tempest.tests import base
from tempest.tests import fake_config


class TestMinClientVersion(base.TestCase):
    """Tests for the min_client_version decorator.
    """

    def setUp(self):
        super(TestMinClientVersion, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

    def _test_min_version(self, required, installed, expect_skip):

        @cli.min_client_version(client='nova', version=required)
        def fake(self, expect_skip):
            if expect_skip:
                # If we got here, the decorator didn't raise a skipException as
                # expected so we need to fail.
                self.fail('Should not have gotten past the decorator.')

        with mock.patch.object(cli_base, 'execute',
                               return_value=installed) as mock_cmd:
            if expect_skip:
                self.assertRaises(testtools.TestCase.skipException, fake,
                                  self, expect_skip)
            else:
                fake(self, expect_skip)
            mock_cmd.assert_called_once_with('nova', '', params='--version',
                                             cli_dir='/usr/local/bin',
                                             merge_stderr=True)

    def test_min_client_version(self):
        # required, installed, expect_skip
        cases = (('2.17.0', '2.17.0', False),
                 ('2.17.0', '2.18.0', False),
                 ('2.18.0', '2.17.0', True))

        for case in cases:
            self._test_min_version(*case)

    @mock.patch.object(cli_base, 'execute', return_value=' ')
    def test_check_client_version_empty_output(self, mock_execute):
        # Tests that an exception is raised if the command output is empty.
        self.assertRaises(exceptions.TempestException,
                          cli.check_client_version, 'nova', '2.18.0')
