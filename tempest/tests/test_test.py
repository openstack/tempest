# Copyright 2017 IBM Corp
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

import sys

import mock
from oslo_config import cfg
import testtools

from tempest import config
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config


if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest


class LoggingTestResult(testtools.TestResult):

    def __init__(self, log, *args, **kwargs):
        super(LoggingTestResult, self).__init__(*args, **kwargs)
        self.log = log

    def addError(self, test, err=None, details=None):
        self.log.append((test, err, details))


class TestTempestBaseTestClass(base.TestCase):

    def setUp(self):
        super(TestTempestBaseTestClass, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

        class ParentTest(test.BaseTestCase):

            def runTest(self):
                pass

        self.parent_test = ParentTest

    @mock.patch(
        'tempest.common.validation_resources.clear_validation_resources',
        autospec=True)
    def test_resource_cleanup(self, mock_vr):
        cfg.CONF.set_default('neutron', False, 'service_available')
        exp_args = (1, 2,)
        exp_kwargs = {'a': 1, 'b': 2}
        exp_vr = {'keypair': 'kp1', 'floating_ip': 'fip2'}
        mock1 = mock.Mock()
        mock2 = mock.Mock()
        exp_functions = [mock1, mock2]

        class TestWithCleanups(self.parent_test):

            # set fake validation resources
            validation_resources = exp_vr

            # set fake clients
            os_primary = 'os_primary'

            @classmethod
            def resource_setup(cls):
                for fn in exp_functions:
                    cls.addClassResourceCleanup(fn, *exp_args,
                                                **exp_kwargs)

        test_cleanups = TestWithCleanups()
        suite = unittest.TestSuite((test_cleanups,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # No exception raised - error log is empty
        self.assertFalse(log)
        # All stacked resource cleanups invoked
        mock1.assert_called_once_with(*exp_args, **exp_kwargs)
        mock2.assert_called_once_with(*exp_args, **exp_kwargs)
        self.assertEqual(1, mock_vr.call_count)
        # Cleanup stack is empty
        self.assertEqual(0, len(test_cleanups._class_cleanups))
        # Assert vrs are cleaned up
        self.assertIn(mock.call(TestWithCleanups.os_primary, use_neutron=False,
                                **exp_vr), mock_vr.call_args_list)

    @mock.patch(
        'tempest.common.validation_resources.clear_validation_resources',
        autospec=True)
    def test_resource_cleanup_failures(self, mock_vr):
        cfg.CONF.set_default('neutron', False, 'service_available')
        exp_args = (1, 2,)
        exp_kwargs = {'a': 1, 'b': 2}
        exp_vr = {'keypair': 'kp1', 'floating_ip': 'fip2'}
        mock1 = mock.Mock()
        mock1.side_effect = Exception('mock1 resource cleanup failure')
        mock2 = mock.Mock()
        exp_functions = [mock1, mock2]

        class TestWithFailingCleanups(self.parent_test):

            # set fake validation resources
            validation_resources = exp_vr

            # set fake clients
            os_primary = 'os_primary'

            @classmethod
            def resource_setup(cls):
                for fn in exp_functions:
                    cls.addClassResourceCleanup(fn, *exp_args,
                                                **exp_kwargs)

        test_cleanups = TestWithFailingCleanups()
        suite = unittest.TestSuite((test_cleanups,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # One multiple exception captured
        self.assertEqual(1, len(log))
        # [0]: test, err, details [1] -> exc_info
        # Type, Exception, traceback [1] -> MultipleException
        found_exc = log[0][1][1]
        self.assertTrue(isinstance(found_exc, testtools.MultipleExceptions))
        self.assertEqual(1, len(found_exc.args))
        # Each arg is exc_info - match messages and order
        self.assertIn('mock1 resource', str(found_exc.args[0][1]))
        # All stacked resource cleanups invoked
        mock1.assert_called_once_with(*exp_args, **exp_kwargs)
        mock2.assert_called_once_with(*exp_args, **exp_kwargs)
        self.assertEqual(1, mock_vr.call_count)
        # Cleanup stack is empty
        self.assertEqual(0, len(test_cleanups._class_cleanups))
        # Assert fake vr are cleaned up
        self.assertIn(mock.call(TestWithFailingCleanups.os_primary,
                                use_neutron=False, **exp_vr),
                      mock_vr.call_args_list)

    def test_super_resource_cleanup_not_invoked(self):

        class BadResourceCleanup(self.parent_test):

            @classmethod
            def resource_cleanup(cls):
                pass

        bad_class = BadResourceCleanup()
        suite = unittest.TestSuite((bad_class,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # One multiple exception captured
        self.assertEqual(1, len(log))
        # [0]: test, err, details [1] -> exc_info
        # Type, Exception, traceback [1] -> RuntimeError
        found_exc = log[0][1][1]
        self.assertTrue(isinstance(found_exc, RuntimeError))
        self.assertIn(BadResourceCleanup.__name__, str(found_exc))
