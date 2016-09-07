# Copyright 2014 Mirantis Inc.
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

import testtools

from tempest.lib import base
from tempest.lib import exceptions


class TestAttr(base.BaseTestCase):

    def test_has_no_attrs(self):
        self.assertEqual(
            'tempest.tests.lib.test_base.TestAttr.test_has_no_attrs',
            self.id()
        )

    @testtools.testcase.attr('foo')
    def test_has_one_attr(self):
        self.assertEqual(
            'tempest.tests.lib.test_base.TestAttr.test_has_one_attr[foo]',
            self.id()
        )

    @testtools.testcase.attr('foo')
    @testtools.testcase.attr('bar')
    def test_has_two_attrs(self):
        self.assertEqual(
            'tempest.tests.lib.test_base.TestAttr.test_has_two_attrs[bar,foo]',
            self.id(),
        )


class TestSetUpClass(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        """Simulate absence of super() call."""

    def setUp(self):
        try:
            # We expect here RuntimeError exception because 'setUpClass'
            # has not called 'super'.
            super(TestSetUpClass, self).setUp()
        except RuntimeError:
            pass
        else:
            raise exceptions.TempestException(
                "If you see this, then expected exception was not raised.")

    def test_setup_class_raises_runtime_error(self):
        """No-op test just to call setUp."""
