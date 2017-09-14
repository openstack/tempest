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

from tempest import clients
from tempest import config
from tempest.lib.common import validation_resources as vr
from tempest.lib import exceptions as lib_exc
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_credentials
from tempest.tests.lib.services import registry_fixture


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


class TestValidationResources(base.TestCase):

    validation_resources_module = 'tempest.lib.common.validation_resources'

    def setUp(self):
        super(TestValidationResources, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.useFixture(registry_fixture.RegistryFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

        class TestTestClass(test.BaseTestCase):
            pass

        self.test_test_class = TestTestClass

    def test_validation_resources_no_validation(self):
        cfg.CONF.set_default('run_validation', False, 'validation')
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        vr = self.test_test_class.get_class_validation_resources(osclients)
        self.assertIsNone(vr)

    def test_validation_resources_exists(self):
        cfg.CONF.set_default('run_validation', True, 'validation')
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        expected_vr = 'expected_validation_resources'
        self.test_test_class._validation_resources[osclients] = expected_vr
        obtained_vr = self.test_test_class.get_class_validation_resources(
            osclients)
        self.assertEqual(expected_vr, obtained_vr)

    @mock.patch(validation_resources_module + '.create_validation_resources',
                autospec=True)
    def test_validation_resources_new(self, mock_create_vr):
        cfg.CONF.set_default('run_validation', True, 'validation')
        cfg.CONF.set_default('neutron', True, 'service_available')
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        expected_vr = {'expected_validation_resources': None}
        mock_create_vr.return_value = expected_vr
        with mock.patch.object(
                self.test_test_class,
                'addClassResourceCleanup') as mock_add_class_cleanup:
            obtained_vr = self.test_test_class.get_class_validation_resources(
                osclients)
            self.assertEqual(1, mock_add_class_cleanup.call_count)
            self.assertEqual(mock.call(vr.clear_validation_resources,
                                       osclients,
                                       use_neutron=True,
                                       **expected_vr),
                             mock_add_class_cleanup.call_args)
        self.assertEqual(mock_create_vr.call_count, 1)
        self.assertIn(osclients, mock_create_vr.call_args_list[0][0])
        self.assertEqual(expected_vr, obtained_vr)
        self.assertIn(osclients, self.test_test_class._validation_resources)
        self.assertEqual(expected_vr,
                         self.test_test_class._validation_resources[osclients])

    def test_validation_resources_invalid_config(self):
        invalid_version = 999
        cfg.CONF.set_default('run_validation', True, 'validation')
        cfg.CONF.set_default('ip_version_for_ssh', invalid_version,
                             'validation')
        cfg.CONF.set_default('neutron', True, 'service_available')
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        with testtools.ExpectedException(
                lib_exc.InvalidConfiguration,
                value_re='^.*\n.*' + str(invalid_version)):
            self.test_test_class.get_class_validation_resources(osclients)

    @mock.patch(validation_resources_module + '.create_validation_resources',
                autospec=True)
    def test_validation_resources_invalid_config_nova_net(self,
                                                          mock_create_vr):
        invalid_version = 999
        cfg.CONF.set_default('run_validation', True, 'validation')
        cfg.CONF.set_default('ip_version_for_ssh', invalid_version,
                             'validation')
        cfg.CONF.set_default('neutron', False, 'service_available')
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        expected_vr = {'expected_validation_resources': None}
        mock_create_vr.return_value = expected_vr
        obtained_vr = self.test_test_class.get_class_validation_resources(
            osclients)
        self.assertEqual(mock_create_vr.call_count, 1)
        self.assertIn(osclients, mock_create_vr.call_args_list[0][0])
        self.assertEqual(expected_vr, obtained_vr)
        self.assertIn(osclients, self.test_test_class._validation_resources)
        self.assertEqual(expected_vr,
                         self.test_test_class._validation_resources[osclients])

    @mock.patch(validation_resources_module + '.create_validation_resources',
                autospec=True)
    @mock.patch(validation_resources_module + '.clear_validation_resources',
                autospec=True)
    def test_validation_resources_fixture(self, mock_clean_vr, mock_create_vr):

        class TestWithRun(self.test_test_class):

            def runTest(self):
                pass

        cfg.CONF.set_default('run_validation', True, 'validation')
        test_case = TestWithRun()
        creds = fake_credentials.FakeKeystoneV3Credentials()
        osclients = clients.Manager(creds)
        test_case.get_test_validation_resources(osclients)
        self.assertEqual(1, mock_create_vr.call_count)
        self.assertEqual(0, mock_clean_vr.call_count)


class TestSetNetworkResources(base.TestCase):

    def setUp(self):
        super(TestSetNetworkResources, self).setUp()

        class ParentTest(test.BaseTestCase):

            @classmethod
            def setup_credentials(cls):
                cls.set_network_resources(dhcp=True)
                super(ParentTest, cls).setup_credentials()

            def runTest(self):
                pass

        self.parent_class = ParentTest

    def test_set_network_resources_child_only(self):

        class ChildTest(self.parent_class):

            @classmethod
            def setup_credentials(cls):
                cls.set_network_resources(router=True)
                super(ChildTest, cls).setup_credentials()

        child_test = ChildTest()
        child_test.setUpClass()
        # Assert that the parents network resources are not set
        self.assertFalse(child_test._network_resources['dhcp'])
        # Assert that the child network resources are set
        self.assertTrue(child_test._network_resources['router'])

    def test_set_network_resources_right_order(self):

        class ChildTest(self.parent_class):

            @classmethod
            def setup_credentials(cls):
                super(ChildTest, cls).setup_credentials()
                cls.set_network_resources(router=True)

        child_test = ChildTest()
        with testtools.ExpectedException(RuntimeError,
                                         value_re='set_network_resources'):
            child_test.setUpClass()

    def test_set_network_resources_children(self):

        class ChildTest(self.parent_class):

            @classmethod
            def setup_credentials(cls):
                cls.set_network_resources(router=True)
                super(ChildTest, cls).setup_credentials()

        class GrandChildTest(ChildTest):
            pass

        # Invoke setupClass on both and check that the setup_credentials
        # call check mechanism does not report any false negative.
        child_test = ChildTest()
        child_test.setUpClass()
        grandchild_test = GrandChildTest()
        grandchild_test.setUpClass()


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

    def test_resource_cleanup(self):
        cfg.CONF.set_default('neutron', False, 'service_available')
        exp_args = (1, 2,)
        exp_kwargs = {'a': 1, 'b': 2}
        mock1 = mock.Mock()
        mock2 = mock.Mock()
        exp_functions = [mock1, mock2]

        class TestWithCleanups(self.parent_test):

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
        # Cleanup stack is empty
        self.assertEqual(0, len(test_cleanups._class_cleanups))

    def test_resource_cleanup_failures(self):
        cfg.CONF.set_default('neutron', False, 'service_available')
        exp_args = (1, 2,)
        exp_kwargs = {'a': 1, 'b': 2}
        mock1 = mock.Mock()
        mock1.side_effect = Exception('mock1 resource cleanup failure')
        mock2 = mock.Mock()
        mock3 = mock.Mock()
        mock3.side_effect = Exception('mock3 resource cleanup failure')
        exp_functions = [mock1, mock2, mock3]

        class TestWithFailingCleanups(self.parent_test):

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
        self.assertEqual(2, len(found_exc.args))
        # Each arg is exc_info - match messages and order
        self.assertIn('mock3 resource', str(found_exc.args[0][1]))
        self.assertIn('mock1 resource', str(found_exc.args[1][1]))
        # All stacked resource cleanups invoked
        mock1.assert_called_once_with(*exp_args, **exp_kwargs)
        mock2.assert_called_once_with(*exp_args, **exp_kwargs)
        # Cleanup stack is empty
        self.assertEqual(0, len(test_cleanups._class_cleanups))

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

    def test_super_skip_checks_not_invoked(self):

        class BadSkipChecks(self.parent_test):

            @classmethod
            def skip_checks(cls):
                pass

        bad_class = BadSkipChecks()
        with testtools.ExpectedException(
                RuntimeError,
                value_re='^.* ' + BadSkipChecks.__name__):
            bad_class.setUpClass()

    def test_super_setup_credentials_not_invoked(self):

        class BadSetupCredentials(self.parent_test):

            @classmethod
            def skip_checks(cls):
                pass

        bad_class = BadSetupCredentials()
        with testtools.ExpectedException(
                RuntimeError,
                value_re='^.* ' + BadSetupCredentials.__name__):
            bad_class.setUpClass()

    def test_grandparent_skip_checks_not_invoked(self):

        class BadSkipChecks(self.parent_test):

            @classmethod
            def skip_checks(cls):
                pass

        class SonOfBadSkipChecks(BadSkipChecks):
            pass

        bad_class = SonOfBadSkipChecks()
        with testtools.ExpectedException(
                RuntimeError,
                value_re='^.* ' + SonOfBadSkipChecks.__name__):
            bad_class.setUpClass()
