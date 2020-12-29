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

import fixtures
from oslo_config import cfg
import testtools

from tempest.common import utils
from tempest import config
from tempest import exceptions
from tempest import test
from tempest.tests import base
from tempest.tests import fake_config


class BaseDecoratorsTest(base.TestCase):
    def setUp(self):
        super(BaseDecoratorsTest, self).setUp()
        self.config_fixture = self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)


class TestServicesDecorator(BaseDecoratorsTest):
    def _test_services_helper(self, *decorator_args):
        class TestFoo(test.BaseTestCase):
            @utils.services(*decorator_args)
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
        self.useFixture(fixtures.MockPatchObject(test.CONF.service_available,
                                                 'cinder', False))
        self.assertRaises(testtools.TestCase.skipException,
                          self._test_services_helper, 'compute',
                          'volume')

    def test_services_list(self):
        service_list = utils.get_service_list()
        for service in service_list:
            try:
                self._test_services_helper(service)
            except exceptions.InvalidServiceTag:
                self.fail('%s is not listed in the valid service tag list'
                          % service)
            except KeyError:
                # NOTE(mtreinish): This condition is to test for an entry in
                # the outer decorator list but not in the service_list dict.
                # However, because we're looping over the service_list dict
                # it's unlikely we'll trigger this. So manual review is still
                # need for the list in the outer decorator.
                self.fail('%s is in the list of valid service tags but there '
                          'is no corresponding entry in the dict returned from'
                          ' get_service_list()' % service)
            except testtools.TestCase.skipException:
                # Test didn't raise an exception because of an incorrect list
                # entry so move onto the next entry
                continue


class TestRequiresExtDecorator(BaseDecoratorsTest):
    def setUp(self):
        super(TestRequiresExtDecorator, self).setUp()
        cfg.CONF.set_default('api_extensions', ['enabled_ext', 'another_ext'],
                             'compute-feature-enabled')

    def _test_requires_ext_helper(self, expected_to_skip=True,
                                  **decorator_args):
        class TestFoo(test.BaseTestCase):
            @utils.requires_ext(**decorator_args)
            def test_bar(self):
                return 0

        t = TestFoo('test_bar')
        if expected_to_skip:
            self.assertRaises(testtools.TestCase.skipException, t.test_bar)
        else:
            try:
                self.assertEqual(t.test_bar(), 0)
            except testtools.TestCase.skipException:
                # We caught a skipException but we didn't expect to skip
                # this test so raise a hard test failure instead.
                raise testtools.TestCase.failureException(
                    "Not supposed to skip")

    def test_requires_ext_decorator(self):
        self._test_requires_ext_helper(expected_to_skip=False,
                                       extension='enabled_ext',
                                       service='compute')

    def test_requires_ext_decorator_disabled_ext(self):
        self._test_requires_ext_helper(extension='disabled_ext',
                                       service='compute')

    def test_requires_ext_decorator_with_all_ext_enabled(self):
        cfg.CONF.set_default('api_extensions', ['all'],
                             group='compute-feature-enabled')
        self._test_requires_ext_helper(expected_to_skip=False,
                                       extension='random_ext',
                                       service='compute')

    def test_requires_ext_decorator_bad_service(self):
        self.assertRaises(KeyError,
                          self._test_requires_ext_helper,
                          extension='enabled_ext',
                          service='bad_service')
