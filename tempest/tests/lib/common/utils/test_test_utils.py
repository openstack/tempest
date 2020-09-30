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

import time
from unittest import mock


from tempest.lib.common import thread
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

    def test_call_and_ignore_notfound_exc_when_serverfault_raised(self):
        calls = []

        def raise_serverfault():
            calls.append('call')
            raise exceptions.ServerFault()
        self.assertRaises(exceptions.ServerFault,
                          test_utils.call_and_ignore_notfound_exc,
                          raise_serverfault)
        self.assertEqual(3, len(calls))

    def test_call_and_ignore_notfound_exc(self):
        m = mock.Mock(return_value=42)
        args, kwargs = (1,), {'1': None}
        self.assertEqual(
            42, test_utils.call_and_ignore_notfound_exc(m, *args, **kwargs))
        m.assert_called_once_with(*args, **kwargs)


class TestCallUntilTrue(base.TestCase):

    def test_call_until_true_when_true_at_first_call(self):
        """func returns True at first call

        """
        self._test_call_until_true(return_values=[True],
                                   duration=30.,
                                   time_sequence=[10., 60.])

    def test_call_until_true_when_true_before_timeout(self):
        """func returns false at first call, then True before timeout

        """
        self._test_call_until_true(return_values=[False, True],
                                   duration=30.,
                                   time_sequence=[10., 39., 41.])

    def test_call_until_true_when_never_true_before_timeout(self):
        """func returns false, then false, just before timeout

        """
        self._test_call_until_true(return_values=[False, False],
                                   duration=30.,
                                   time_sequence=[10., 39., 41.])

    def test_call_until_true_with_params(self):
        """func is called using given parameters

        """
        self._test_call_until_true(return_values=[False, True],
                                   duration=30.,
                                   time_sequence=[10., 30., 60.],
                                   args=(1, 2),
                                   kwargs=dict(foo='bar', bar='foo'))

    def _test_call_until_true(self, return_values, duration, time_sequence,
                              args=None, kwargs=None):
        """Test call_until_true function

        :param return_values: list of booleans values to be returned
        each time given function is called. If any of these values
        is not consumed by calling the function the test fails.
        The list must contain a sequence of False items terminated
        by a single True or False
        :param duration: parameter passed to call_until_true function
        (a floating point value).
        :param time_sequence: sequence of time values returned by
        mocked time.time function used to trigger call_until_true
        behavior when handling timeout condition. The sequence must
        contain the exact number of values expected to be consumed by
        each time call_until_true calls time.time function.
        :param args: sequence of positional arguments to be passed
        to call_until_true function.
        :param kwargs: sequence of named arguments to be passed
        to call_until_true function.
        """

        # all values except the last are False
        self.assertEqual([False] * len(return_values[:-1]), return_values[:-1])
        # last value can be True or False
        self.assertIn(return_values[-1], [True, False])

        # GIVEN
        func = mock.Mock(side_effect=return_values)
        sleep = 10.  # this value has no effect as time.sleep is being mocked
        sleep_func = self.patch('time.sleep')
        time_func = self._patch_time(time_sequence)
        args = args or tuple()
        kwargs = kwargs or dict()

        # WHEN
        result = test_utils.call_until_true(func, duration, sleep,
                                            *args, **kwargs)
        # THEN

        # It must return last returned value
        self.assertIs(return_values[-1], result)

        self._test_func_calls(func, return_values, *args, **kwargs)
        self._test_sleep_calls(sleep_func, return_values, sleep)
        # The number of times time.time is called is not relevant as a
        # requirement of call_until_true. What is instead relevant is that
        # call_until_true use a mocked function to make the test reliable
        # and the test actually provide the right sequence of numbers to
        # reproduce the behavior has to be tested
        self._assert_called_n_times(time_func, len(time_sequence))

    def _patch_time(self, time_sequence):
        # Iterator over time sequence
        time_iterator = iter(time_sequence)
        # Preserve original time.time() behavior for other threads
        original_time = time.time
        thread_id = thread.get_ident()

        def mocked_time():
            if thread.get_ident() == thread_id:
                # Test thread => return time sequence values
                return next(time_iterator)
            else:
                # Other threads => call original time function
                return original_time()

        return self.patch('time.time', side_effect=mocked_time)

    def _test_func_calls(self, func, return_values, *args, **kwargs):
        self._assert_called_n_times(func, len(return_values), *args, **kwargs)

    def _test_sleep_calls(self, sleep_func, return_values, sleep):
        # count first consecutive False
        expected_count = 0
        for value in return_values:
            if value:
                break
            expected_count += 1
        self._assert_called_n_times(sleep_func, expected_count, sleep)

    def _assert_called_n_times(self, mock_func, expected_count, *args,
                               **kwargs):
        calls = [mock.call(*args, **kwargs)] * expected_count
        self.assertEqual(expected_count, mock_func.call_count)
        mock_func.assert_has_calls(calls)
