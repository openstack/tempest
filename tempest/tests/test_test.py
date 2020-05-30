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

import os
import sys
from unittest import mock

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

    @mock.patch('tempest.common.credentials_factory.is_admin_available',
                autospec=True, return_value=True)
    def test_skip_checks_admin(self, mock_iaa):
        identity_version = 'identity_version'

        class NeedAdmin(self.parent_test):
            credentials = ['admin']

            @classmethod
            def get_identity_version(cls):
                return identity_version

        NeedAdmin().skip_checks()
        mock_iaa.assert_called_once_with('identity_version')

    @mock.patch('tempest.common.credentials_factory.is_admin_available',
                autospec=True, return_value=False)
    def test_skip_checks_admin_not_available(self, mock_iaa):
        identity_version = 'identity_version'

        class NeedAdmin(self.parent_test):
            credentials = ['admin']

            @classmethod
            def get_identity_version(cls):
                return identity_version

        with testtools.ExpectedException(testtools.testcase.TestSkipped):
            NeedAdmin().skip_checks()
        mock_iaa.assert_called_once_with('identity_version')

    def test_skip_checks_identity_v2_not_available(self):
        cfg.CONF.set_default('api_v2', False, 'identity-feature-enabled')

        class NeedV2(self.parent_test):
            identity_version = 'v2'

        with testtools.ExpectedException(testtools.testcase.TestSkipped):
            NeedV2().skip_checks()

    def test_skip_checks_identity_v3_not_available(self):
        cfg.CONF.set_default('api_v3', False, 'identity-feature-enabled')

        class NeedV3(self.parent_test):
            identity_version = 'v3'

        with testtools.ExpectedException(testtools.testcase.TestSkipped):
            NeedV3().skip_checks()

    def test_setup_credentials_all(self):
        expected_creds = ['string', ['list', 'role1', 'role2']]

        class AllCredentials(self.parent_test):
            credentials = expected_creds

        expected_clients = 'clients'
        with mock.patch.object(
                AllCredentials,
                'get_client_manager') as mock_get_client_manager:
            mock_get_client_manager.return_value = expected_clients
            all_creds = AllCredentials()
            all_creds.setup_credentials()
        self.assertTrue(hasattr(all_creds, 'os_string'))
        self.assertEqual(expected_clients, all_creds.os_string)
        self.assertTrue(hasattr(all_creds, 'os_roles_list'))
        self.assertEqual(expected_clients, all_creds.os_roles_list)
        self.assertEqual(2, mock_get_client_manager.call_count)
        self.assertEqual(
            expected_creds[0],
            mock_get_client_manager.mock_calls[0][2]['credential_type'])
        self.assertEqual(
            expected_creds[1][1:],
            mock_get_client_manager.mock_calls[1][2]['roles'])

    def test_setup_class_overwritten(self):

        class OverridesSetup(self.parent_test):

            @classmethod
            def setUpClass(cls):  # noqa
                pass

        overrides_setup = OverridesSetup()
        suite = unittest.TestSuite((overrides_setup,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # Record 0, test (error holder). The error generates during test run.
        self.assertIn('runTest', str(log[0][0]))
        # Record 0, traceback
        self.assertRegex(
            str(log[0][2]['traceback']).replace('\n', ' '),
            RuntimeError.__name__ + ': .* ' + OverridesSetup.__name__)


class TestTempestBaseTestClassFixtures(base.TestCase):

    SETUP_FIXTURES = [test.BaseTestCase.setUpClass.__name__,
                      test.BaseTestCase.skip_checks.__name__,
                      test.BaseTestCase.setup_credentials.__name__,
                      test.BaseTestCase.setup_clients.__name__,
                      test.BaseTestCase.resource_setup.__name__]
    TEARDOWN_FIXTURES = [test.BaseTestCase.tearDownClass.__name__,
                         test.BaseTestCase.resource_cleanup.__name__,
                         test.BaseTestCase.clear_credentials.__name__]

    def setUp(self):
        super(TestTempestBaseTestClassFixtures, self).setUp()
        self.mocks = {}
        for fix in self.SETUP_FIXTURES + self.TEARDOWN_FIXTURES:
            self.mocks[fix] = mock.Mock()

        def tracker_builder(name):

            def tracker(cls):
                # Track that the fixture was invoked
                cls.fixtures_invoked.append(name)
                # Run the fixture
                getattr(super(TestWithClassFixtures, cls), name)()
                # Run a mock we can use for side effects
                self.mocks[name]()

            return tracker

        class TestWithClassFixtures(test.BaseTestCase):

            credentials = []
            fixtures_invoked = []

            def runTest(_self):
                pass

        # Decorate all test class fixtures with tracker_builder
        for method_name in self.SETUP_FIXTURES + self.TEARDOWN_FIXTURES:
            setattr(TestWithClassFixtures, method_name,
                    classmethod(tracker_builder(method_name)))

        self.test = TestWithClassFixtures()

    def test_no_error_flow(self):
        # If all setup fixtures are executed, all cleanup fixtures are
        # executed too
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        self.assertEqual(self.SETUP_FIXTURES + self.TEARDOWN_FIXTURES,
                         self.test.fixtures_invoked)

    def test_skip_only(self):
        # If a skip condition is hit in the test, no credentials or resource
        # is provisioned / cleaned-up
        self.mocks['skip_checks'].side_effect = (
            testtools.TestCase.skipException())
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If we trigger a skip condition, teardown is not invoked at all
        self.assertEqual((self.SETUP_FIXTURES[:2] +
                          [self.TEARDOWN_FIXTURES[0]]),
                         self.test.fixtures_invoked)

    def test_skip_credentials_fails(self):
        expected_exc = 'sc exploded'
        self.mocks['setup_credentials'].side_effect = Exception(expected_exc)
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If setup_credentials explodes, we invoked teardown class and
        # clear credentials, and re-raise
        self.assertEqual((self.SETUP_FIXTURES[:3] +
                          [self.TEARDOWN_FIXTURES[i] for i in (0, 2)]),
                         self.test.fixtures_invoked)
        found_exc = log[0][1][1]
        self.assertIn(expected_exc, str(found_exc))

    def test_skip_credentials_fails_clear_fails(self):
        # If cleanup fails on failure, we log the exception and do not
        # re-raise it. Note that since the exception happens outside of
        # the Tempest test setUp, logging is not captured on the Tempest
        # test side, it will be captured by the unit test instead.
        expected_exc = 'sc exploded'
        clear_exc = 'clear exploded'
        self.mocks['setup_credentials'].side_effect = Exception(expected_exc)
        self.mocks['clear_credentials'].side_effect = Exception(clear_exc)
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If setup_credentials explodes, we invoked teardown class and
        # clear credentials, and re-raise
        self.assertEqual((self.SETUP_FIXTURES[:3] +
                          [self.TEARDOWN_FIXTURES[i] for i in (0, 2)]),
                         self.test.fixtures_invoked)
        found_exc = log[0][1][1]
        self.assertIn(expected_exc, str(found_exc))
        # Since log capture depends on OS_LOG_CAPTURE, we can only assert if
        # logging was captured
        if os.environ.get('OS_LOG_CAPTURE'):
            self.assertIn(clear_exc, self.log_fixture.logger.output)

    def test_skip_credentials_clients_resources_credentials_clear_fails(self):
        # If cleanup fails with no previous failure, we re-raise the exception.
        expected_exc = 'clear exploded'
        self.mocks['clear_credentials'].side_effect = Exception(expected_exc)
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If setup_credentials explodes, we invoked teardown class and
        # clear credentials, and re-raise
        self.assertEqual(self.SETUP_FIXTURES + self.TEARDOWN_FIXTURES,
                         self.test.fixtures_invoked)
        found_exc = log[0][1][1]
        self.assertIn(expected_exc, str(found_exc))

    def test_skip_credentials_clients_fails(self):
        expected_exc = 'clients exploded'
        self.mocks['setup_clients'].side_effect = Exception(expected_exc)
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If setup_clients explodes, we invoked teardown class and
        # clear credentials, and re-raise
        self.assertEqual((self.SETUP_FIXTURES[:4] +
                          [self.TEARDOWN_FIXTURES[i] for i in (0, 2)]),
                         self.test.fixtures_invoked)
        found_exc = log[0][1][1]
        self.assertIn(expected_exc, str(found_exc))

    def test_skip_credentials_clients_resources_fails(self):
        expected_exc = 'resource setup exploded'
        self.mocks['resource_setup'].side_effect = Exception(expected_exc)
        suite = unittest.TestSuite((self.test,))
        log = []
        result = LoggingTestResult(log)
        suite.run(result)
        # If resource_setup explodes, we invoked teardown class and
        # clear credentials and resource cleanup, and re-raise
        self.assertEqual(self.SETUP_FIXTURES + self.TEARDOWN_FIXTURES,
                         self.test.fixtures_invoked)
        found_exc = log[0][1][1]
        self.assertIn(expected_exc, str(found_exc))
