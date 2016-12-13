# Copyright 2016 OpenStack Foundation
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
import mock

from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
from tempest.tests import base


class TestTestUtils(base.TestCase):

    def test_find_test_caller_test_case(self):
        # Calling it from here should give us the method we're in.
        self.assertEqual('TestTestUtils:test_find_test_caller_test_case',
                         test_utils.find_test_caller())

    def test_find_test_caller_setup_self(self):
        def setUp(self):
            return test_utils.find_test_caller()
        self.assertEqual('TestTestUtils:setUp', setUp(self))

    def test_find_test_caller_setup_no_self(self):
        def setUp():
            return test_utils.find_test_caller()
        self.assertEqual(':setUp', setUp())

    def test_find_test_caller_setupclass_cls(self):
        def setUpClass(cls):  # noqa
            return test_utils.find_test_caller()
        self.assertEqual('TestTestUtils:setUpClass',
                         setUpClass(self.__class__))

    def test_find_test_caller_teardown_self(self):
        def tearDown(self):
            return test_utils.find_test_caller()
        self.assertEqual('TestTestUtils:tearDown', tearDown(self))

    def test_find_test_caller_teardown_no_self(self):
        def tearDown():
            return test_utils.find_test_caller()
        self.assertEqual(':tearDown', tearDown())

    def test_find_test_caller_teardown_class(self):
        def tearDownClass(cls):  # noqa
            return test_utils.find_test_caller()
        self.assertEqual('TestTestUtils:tearDownClass',
                         tearDownClass(self.__class__))

    def test_call_and_ignore_notfound_exc_when_notfound_raised(self):
        def raise_not_found():
            raise exceptions.NotFound()
        self.assertIsNone(
            test_utils.call_and_ignore_notfound_exc(raise_not_found))

    def test_call_and_ignore_notfound_exc_when_value_error_raised(self):
        def raise_value_error():
            raise ValueError()
        self.assertRaises(ValueError, test_utils.call_and_ignore_notfound_exc,
                          raise_value_error)

    def test_call_and_ignore_notfound_exc(self):
        m = mock.Mock(return_value=42)
        args, kwargs = (1,), {'1': None}
        self.assertEqual(
            42, test_utils.call_and_ignore_notfound_exc(m, *args, **kwargs))
        m.assert_called_once_with(*args, **kwargs)
