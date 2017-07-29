# Copyright 2015 NEC Corporation.  All rights reserved.
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

from oslo_config import cfg
import six
import testtools

from tempest.api.compute import base as compute_base
from tempest import config
from tempest.lib import exceptions
from tempest.tests import base
from tempest.tests import fake_config


class VersionTestNoneTolatest(compute_base.BaseV2ComputeTest):
    min_microversion = None
    max_microversion = 'latest'


class VersionTestNoneTo2_2(compute_base.BaseV2ComputeTest):
    min_microversion = None
    max_microversion = '2.2'


class VersionTest2_3ToLatest(compute_base.BaseV2ComputeTest):
    min_microversion = '2.3'
    max_microversion = 'latest'


class VersionTest2_5To2_10(compute_base.BaseV2ComputeTest):
    min_microversion = '2.5'
    max_microversion = '2.10'


class VersionTest2_10To2_10(compute_base.BaseV2ComputeTest):
    min_microversion = '2.10'
    max_microversion = '2.10'


class InvalidVersionTest(compute_base.BaseV2ComputeTest):
    min_microversion = '2.11'
    max_microversion = '2.1'


class TestMicroversionsTestsClass(base.TestCase):

    def setUp(self):
        super(TestMicroversionsTestsClass, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

    def _test_version(self, cfg_min, cfg_max,
                      expected_pass_tests,
                      expected_skip_tests):
        cfg.CONF.set_default('min_microversion',
                             cfg_min, group='compute')
        cfg.CONF.set_default('max_microversion',
                             cfg_max, group='compute')
        try:
            for test_class in expected_pass_tests:
                test_class.skip_checks()
            for test_class in expected_skip_tests:
                self.assertRaises(testtools.TestCase.skipException,
                                  test_class.skip_checks)
        except testtools.TestCase.skipException as e:
            raise testtools.TestCase.failureException(six.text_type(e))

    def test_config_version_none_none(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTestNoneTo2_2]
        expected_skip_tests = [VersionTest2_3ToLatest, VersionTest2_5To2_10,
                               VersionTest2_10To2_10]
        self._test_version(None, None,
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_none_23(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTestNoneTo2_2,
                               VersionTest2_3ToLatest]
        expected_skip_tests = [VersionTest2_5To2_10, VersionTest2_10To2_10]
        self._test_version(None, '2.3',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_22_latest(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTestNoneTo2_2,
                               VersionTest2_3ToLatest, VersionTest2_5To2_10,
                               VersionTest2_10To2_10]
        expected_skip_tests = []
        self._test_version('2.2', 'latest',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_22_23(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTestNoneTo2_2,
                               VersionTest2_3ToLatest]
        expected_skip_tests = [VersionTest2_5To2_10, VersionTest2_10To2_10]
        self._test_version('2.2', '2.3',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_210_210(self):
        expected_pass_tests = [VersionTestNoneTolatest,
                               VersionTest2_3ToLatest,
                               VersionTest2_5To2_10,
                               VersionTest2_10To2_10]
        expected_skip_tests = [VersionTestNoneTo2_2]
        self._test_version('2.10', '2.10',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_none_latest(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTestNoneTo2_2,
                               VersionTest2_3ToLatest, VersionTest2_5To2_10,
                               VersionTest2_10To2_10]
        expected_skip_tests = []
        self._test_version(None, 'latest',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_version_latest_latest(self):
        expected_pass_tests = [VersionTestNoneTolatest, VersionTest2_3ToLatest]
        expected_skip_tests = [VersionTestNoneTo2_2, VersionTest2_5To2_10,
                               VersionTest2_10To2_10]
        self._test_version('latest', 'latest',
                           expected_pass_tests,
                           expected_skip_tests)

    def test_config_invalid_version(self):
        cfg.CONF.set_default('min_microversion',
                             '2.5', group='compute')
        cfg.CONF.set_default('max_microversion',
                             '2.1', group='compute')
        self.assertRaises(exceptions.InvalidAPIVersionRange,
                          VersionTestNoneTolatest.skip_checks)

    def test_config_version_invalid_test_version(self):
        cfg.CONF.set_default('min_microversion',
                             None, group='compute')
        cfg.CONF.set_default('max_microversion',
                             '2.13', group='compute')
        self.assertRaises(exceptions.InvalidAPIVersionRange,
                          InvalidVersionTest.skip_checks)
