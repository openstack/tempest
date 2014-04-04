# Copyright 2013 IBM Corp.
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
import testtools

from oslo.config import cfg

from tempest import config
from tempest import exceptions
from tempest.openstack.common.fixture import mockpatch
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config


class BaseDecoratorsTest(base.TestCase):
    def setUp(self):
        super(BaseDecoratorsTest, self).setUp()
        self.config_fixture = self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)


class TestAttrDecorator(BaseDecoratorsTest):
    def _test_attr_helper(self, expected_attrs, **decorator_args):
        @test.attr(**decorator_args)
        def foo():
            pass

        # By our test.attr decorator the attribute __testtools_attrs will be
        # set only for 'type' argument, so we test it first.
        if 'type' in decorator_args:
            # this is what testtools sets
            self.assertEqual(getattr(foo, '__testtools_attrs'),
                             set(expected_attrs))

    def test_attr_without_type(self):
        self._test_attr_helper(expected_attrs='baz', bar='baz')

    def test_attr_decorator_with_smoke_type(self):
        # smoke passed as type, so smoke and gate must have been set.
        self._test_attr_helper(expected_attrs=['smoke', 'gate'], type='smoke')

    def test_attr_decorator_with_list_type(self):
        # if type is 'smoke' we'll get the original list of types plus 'gate'
        self._test_attr_helper(expected_attrs=['smoke', 'foo', 'gate'],
                               type=['smoke', 'foo'])

    def test_attr_decorator_with_unknown_type(self):
        self._test_attr_helper(expected_attrs=['foo'], type='foo')

    def test_attr_decorator_with_duplicated_type(self):
        self._test_attr_helper(expected_attrs=['foo'], type=['foo', 'foo'])


class TestServicesDecorator(BaseDecoratorsTest):
    def _test_services_helper(self, *decorator_args):
        class TestFoo(test.BaseTestCase):
            @test.services(*decorator_args)
            def test_bar(self):
                return 0

        t = TestFoo('test_bar')
        self.assertEqual(set(decorator_args), getattr(t.test_bar,
                                                      '__testtools_attrs'))
        self.assertEqual(t.test_bar(), 0)

    def test_services_decorator_with_single_service(self):
        self._test_services_helper('compute')

    def test_services_decorator_with_multiple_services(self):
        self._test_services_helper('compute', 'network')

    def test_services_decorator_with_duplicated_service(self):
        self._test_services_helper('compute', 'compute')

    def test_services_decorator_with_invalid_service(self):
        self.assertRaises(exceptions.InvalidServiceTag,
                          self._test_services_helper, 'compute',
                          'bad_service')

    def test_services_decorator_with_service_valid_and_unavailable(self):
        self.useFixture(mockpatch.PatchObject(test.CONF.service_available,
                                              'cinder', False))
        self.assertRaises(testtools.TestCase.skipException,
                          self._test_services_helper, 'compute',
                          'volume')


class TestStressDecorator(BaseDecoratorsTest):
    def _test_stresstest_helper(self, expected_frequency='process',
                                expected_inheritance=False,
                                **decorator_args):
        @test.stresstest(**decorator_args)
        def foo():
            pass
        self.assertEqual(getattr(foo, 'st_class_setup_per'),
                         expected_frequency)
        self.assertEqual(getattr(foo, 'st_allow_inheritance'),
                         expected_inheritance)
        self.assertEqual(set(['stress']), getattr(foo, '__testtools_attrs'))

    def test_stresstest_decorator_default(self):
        self._test_stresstest_helper()

    def test_stresstest_decorator_class_setup_frequency(self):
        self._test_stresstest_helper('process', class_setup_per='process')

    def test_stresstest_decorator_class_setup_frequency_non_default(self):
        self._test_stresstest_helper(expected_frequency='application',
                                     class_setup_per='application')

    def test_stresstest_decorator_set_frequency_and_inheritance(self):
        self._test_stresstest_helper(expected_frequency='application',
                                     expected_inheritance=True,
                                     class_setup_per='application',
                                     allow_inheritance=True)


class TestSkipBecauseDecorator(BaseDecoratorsTest):
    def _test_skip_because_helper(self, expected_to_skip=True,
                                  **decorator_args):
        class TestFoo(test.BaseTestCase):
            _interface = 'json'

            @test.skip_because(**decorator_args)
            def test_bar(self):
                return 0

        t = TestFoo('test_bar')
        if expected_to_skip:
            self.assertRaises(testtools.TestCase.skipException, t.test_bar)
        else:
            # assert that test_bar returned 0
            self.assertEqual(TestFoo('test_bar').test_bar(), 0)

    def test_skip_because_bug(self):
        self._test_skip_because_helper(bug='12345')

    def test_skip_because_bug_and_interface_match(self):
        self._test_skip_because_helper(bug='12346', interface='json')

    def test_skip_because_bug_interface_not_match(self):
        self._test_skip_because_helper(expected_to_skip=False,
                                       bug='12347', interface='xml')

    def test_skip_because_bug_and_condition_true(self):
        self._test_skip_because_helper(bug='12348', condition=True)

    def test_skip_because_bug_and_condition_false(self):
        self._test_skip_because_helper(expected_to_skip=False,
                                       bug='12349', condition=False)

    def test_skip_because_bug_condition_false_and_interface_match(self):
        """
        Assure that only condition will be evaluated if both parameters are
        passed.
        """
        self._test_skip_because_helper(expected_to_skip=False,
                                       bug='12350', condition=False,
                                       interface='json')

    def test_skip_because_bug_condition_true_and_interface_not_match(self):
        """
        Assure that only condition will be evaluated if both parameters are
        passed.
        """
        self._test_skip_because_helper(bug='12351', condition=True,
                                       interface='xml')

    def test_skip_because_bug_without_bug_never_skips(self):
        """Never skip without a bug parameter."""
        self._test_skip_because_helper(expected_to_skip=False,
                                       condition=True)
        self._test_skip_because_helper(expected_to_skip=False,
                                       interface='json')

    def test_skip_because_invalid_bug_number(self):
        """Raise ValueError if with an invalid bug number"""
        self.assertRaises(ValueError, self._test_skip_because_helper,
                          bug='critical_bug')


class TestRequiresExtDecorator(BaseDecoratorsTest):
    def setUp(self):
        super(TestRequiresExtDecorator, self).setUp()
        cfg.CONF.set_default('api_extensions', ['enabled_ext', 'another_ext'],
                             'compute-feature-enabled')

    def _test_requires_ext_helper(self, expected_to_skip=True,
                                  **decorator_args):
        class TestFoo(test.BaseTestCase):
            @test.requires_ext(**decorator_args)
            def test_bar(self):
                return 0

        t = TestFoo('test_bar')
        if expected_to_skip:
            self.assertRaises(testtools.TestCase.skipException, t.test_bar)
        else:
            self.assertEqual(t.test_bar(), 0)

    def test_requires_ext_decorator(self):
        self._test_requires_ext_helper(expected_to_skip=False,
                                       extension='enabled_ext',
                                       service='compute')

    def test_requires_ext_decorator_disabled_ext(self):
        self._test_requires_ext_helper(extension='disabled_ext',
                                       service='compute')

    def test_requires_ext_decorator_with_all_ext_enabled(self):
        # disable fixture so the default (all) is used.
        self.config_fixture.cleanUp()
        self._test_requires_ext_helper(expected_to_skip=False,
                                       extension='random_ext',
                                       service='compute')

    def test_requires_ext_decorator_bad_service(self):
        self.assertRaises(KeyError,
                          self._test_requires_ext_helper,
                          extension='enabled_ext',
                          service='bad_service')


class TestSimpleNegativeDecorator(BaseDecoratorsTest):
    @test.SimpleNegativeAutoTest
    class FakeNegativeJSONTest(test.NegativeAutoTest):
        _schema_file = 'fake/schemas/file.json'

    def test_testfunc_exist(self):
        self.assertIn("test_fake_negative", dir(self.FakeNegativeJSONTest))

    @mock.patch('tempest.test.NegativeAutoTest.execute')
    def test_testfunc_calls_execute(self, mock):
        obj = self.FakeNegativeJSONTest("test_fake_negative")
        self.assertIn("test_fake_negative", dir(obj))
        obj.test_fake_negative()
        mock.assert_called_once_with(self.FakeNegativeJSONTest._schema_file)
