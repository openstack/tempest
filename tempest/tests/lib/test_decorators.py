# Copyright 2013 IBM Corp
# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import abc

import mock
import six
import testtools

from tempest.lib import base as test
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.tests import base


class TestAttrDecorator(base.TestCase):
    def _test_attr_helper(self, expected_attrs, **decorator_args):
        @decorators.attr(**decorator_args)
        def foo():
            pass

        # By our decorators.attr decorator the attribute __testtools_attrs
        # will be set only for 'type' argument, so we test it first.
        if 'type' in decorator_args:
            if 'condition' in decorator_args:
                if decorator_args['condition']:
                    # The expected attrs should be in the function.
                    self.assertEqual(set(expected_attrs),
                                     getattr(foo, '__testtools_attrs'))
                else:
                    # The expected attrs should not be in the function.
                    self.assertNotIn('__testtools_attrs', foo)
            else:
                self.assertEqual(set(expected_attrs),
                                 getattr(foo, '__testtools_attrs'))

    def test_attr_without_type(self):
        self._test_attr_helper(expected_attrs='baz', bar='baz')

    def test_attr_decorator_with_list_type(self):
        # if type is 'smoke' we'll get the original list of types
        self._test_attr_helper(expected_attrs=['smoke', 'foo'],
                               type=['smoke', 'foo'])

    def test_attr_decorator_with_unknown_type(self):
        self._test_attr_helper(expected_attrs=['foo'], type='foo')

    def test_attr_decorator_with_duplicated_type(self):
        self._test_attr_helper(expected_attrs=['foo'], type=['foo', 'foo'])

    def test_attr_decorator_condition_false(self):
        self._test_attr_helper(None, type='slow', condition=False)

    def test_attr_decorator_condition_true(self):
        self._test_attr_helper(expected_attrs=['slow'], type='slow',
                               condition=True)


@six.add_metaclass(abc.ABCMeta)
class BaseSkipDecoratorTests(object):

    @abc.abstractmethod
    def _test_skip_helper(self, raise_exception=True, expected_to_skip=True,
                          **decorator_args):
        return

    def test_skip_launchpad_bug(self):
        self._test_skip_helper(bug='12345')

    def test_skip_storyboard_bug(self):
        self._test_skip_helper(bug='1992', bug_type='storyboard')

    def test_skip_bug_without_bug_never_skips(self):
        """Never skip without a bug parameter."""
        self._test_skip_helper(
            raise_exception=False, expected_to_skip=False, condition=True)
        self._test_skip_helper(
            raise_exception=False, expected_to_skip=False)

    def test_skip_invalid_bug_number(self):
        """Raise InvalidParam if with an invalid bug number"""
        self.assertRaises(lib_exc.InvalidParam, self._test_skip_helper,
                          bug='critical_bug')


class TestSkipBecauseDecorator(base.TestCase, BaseSkipDecoratorTests):
    def _test_skip_helper(self, raise_exception=True, expected_to_skip=True,
                          **decorator_args):
        class TestFoo(test.BaseTestCase):
            _interface = 'json'

            @decorators.skip_because(**decorator_args)
            def test_bar(self):
                return 0

        t = TestFoo('test_bar')
        if expected_to_skip:
            e = self.assertRaises(testtools.TestCase.skipException, t.test_bar)
            bug = decorator_args['bug']
            bug_type = decorator_args.get('bug_type', 'launchpad')
            self.assertRegex(
                str(e),
                r'Skipped until bug\: %s.*' % decorators._get_bug_url(
                    bug, bug_type)
            )
        else:
            # assert that test_bar returned 0
            self.assertEqual(TestFoo('test_bar').test_bar(), 0)

    def test_skip_because_launchpad_bug_and_condition_true(self):
        self._test_skip_helper(bug='12348', condition=True)

    def test_skip_because_launchpad_bug_and_condition_false(self):
        self._test_skip_helper(expected_to_skip=False,
                               bug='12349', condition=False)

    def test_skip_because_storyboard_bug_and_condition_false(self):
        self._test_skip_helper(expected_to_skip=False,
                               bug='1992', bug_type='storyboard',
                               condition=False)

    def test_skip_because_storyboard_bug_and_condition_true(self):
        self._test_skip_helper(bug='1992', bug_type='storyboard',
                               condition=True)


class TestUnstableTestDecorator(base.TestCase, BaseSkipDecoratorTests):

    def _test_skip_helper(self, raise_exception=True, expected_to_skip=True,
                          **decorator_args):
        fail_test_reason = "test_bar failed"

        class TestFoo(test.BaseTestCase):

            @decorators.unstable_test(**decorator_args)
            def test_bar(self):
                if raise_exception:
                    raise Exception(fail_test_reason)
                else:
                    return 0

        t = TestFoo('test_bar')
        if expected_to_skip:
            e = self.assertRaises(testtools.TestCase.skipException, t.test_bar)
            bug = decorator_args['bug']
            bug_type = decorator_args.get('bug_type', 'launchpad')
            self.assertRegex(
                str(e),
                r'Marked as unstable and skipped because of bug\: %s.*, '
                'failure was: %s' % (decorators._get_bug_url(bug, bug_type),
                                     fail_test_reason)
            )
        else:
            # assert that test_bar returned 0
            self.assertEqual(TestFoo('test_bar').test_bar(), 0)

    def test_skip_bug_given_exception_not_raised(self):
        self._test_skip_helper(raise_exception=False, expected_to_skip=False,
                               bug='1234')


class TestIdempotentIdDecorator(base.TestCase):
    def _test_helper(self, _id, **decorator_args):
        @decorators.idempotent_id(_id)
        def foo():
            """Docstring"""
            pass

        return foo

    def _test_helper_without_doc(self, _id, **decorator_args):
        @decorators.idempotent_id(_id)
        def foo():
            pass

        return foo

    def test_positive(self):
        _id = data_utils.rand_uuid()
        foo = self._test_helper(_id)
        self.assertIn('id-%s' % _id, getattr(foo, '__testtools_attrs'))
        self.assertTrue(foo.__doc__.startswith('Test idempotent id: %s' % _id))

    def test_positive_without_doc(self):
        _id = data_utils.rand_uuid()
        foo = self._test_helper_without_doc(_id)
        self.assertTrue(foo.__doc__.startswith('Test idempotent id: %s' % _id))

    def test_idempotent_id_not_str(self):
        _id = 42
        self.assertRaises(TypeError, self._test_helper, _id)

    def test_idempotent_id_not_valid_uuid(self):
        _id = '42'
        self.assertRaises(ValueError, self._test_helper, _id)


class TestRelatedBugDecorator(base.TestCase):

    def _get_my_exception(self):
        class MyException(Exception):
            def __init__(self, status_code):
                self.status_code = status_code
        return MyException

    def test_relatedbug_when_no_exception(self):
        f = mock.Mock()
        sentinel = object()

        @decorators.related_bug(bug="1234", status_code=500)
        def test_foo(self):
            f(self)

        test_foo(sentinel)
        f.assert_called_once_with(sentinel)

    def test_relatedbug_when_exception_with_launchpad_bug_type(self):
        """Validate related_bug decorator with bug_type == 'launchpad'"""
        MyException = self._get_my_exception()

        def f(self):
            raise MyException(status_code=500)

        @decorators.related_bug(bug="1234", status_code=500)
        def test_foo(self):
            f(self)

        with mock.patch.object(decorators.LOG, 'error') as m_error:
            self.assertRaises(MyException, test_foo, object())

        m_error.assert_called_once_with(
            mock.ANY, '1234', 'https://launchpad.net/bugs/1234')

    def test_relatedbug_when_exception_with_storyboard_bug_type(self):
        """Validate related_bug decorator with bug_type == 'storyboard'"""
        MyException = self._get_my_exception()

        def f(self):
            raise MyException(status_code=500)

        @decorators.related_bug(bug="1234", status_code=500,
                                bug_type='storyboard')
        def test_foo(self):
            f(self)

        with mock.patch.object(decorators.LOG, 'error') as m_error:
            self.assertRaises(MyException, test_foo, object())

        m_error.assert_called_once_with(
            mock.ANY, '1234', 'https://storyboard.openstack.org/#!/story/1234')

    def test_relatedbug_when_exception_invalid_bug_type(self):
        """Check related_bug decorator raises exc when bug_type is not valid"""
        MyException = self._get_my_exception()

        def f(self):
            raise MyException(status_code=500)

        @decorators.related_bug(bug="1234", status_code=500,
                                bug_type=mock.sentinel.invalid)
        def test_foo(self):
            f(self)

        with mock.patch.object(decorators.LOG, 'error'):
            self.assertRaises(lib_exc.InvalidParam, test_foo, object())

    def test_relatedbug_when_exception_invalid_bug_number(self):
        """Check related_bug decorator raises exc when bug_number != digit"""
        MyException = self._get_my_exception()

        def f(self):
            raise MyException(status_code=500)

        @decorators.related_bug(bug="not a digit", status_code=500,
                                bug_type='launchpad')
        def test_foo(self):
            f(self)

        with mock.patch.object(decorators.LOG, 'error'):
            self.assertRaises(lib_exc.InvalidParam, test_foo, object())
