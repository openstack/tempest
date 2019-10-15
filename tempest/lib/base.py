# Copyright 2012 OpenStack Foundation
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

import fixtures
import pkg_resources
import testtools


def _handle_skip_exception():
    try:
        stestr_version = pkg_resources.parse_version(
            pkg_resources.get_distribution("stestr").version)
        stestr_min = pkg_resources.parse_version('2.5.0')
        new_stestr = (stestr_version >= stestr_min)
        import unittest
        import unittest2
        if sys.version_info >= (3, 5) and new_stestr:
            testtools.TestCase.skipException = unittest.case.SkipTest
        else:
            testtools.TestCase.skipException = unittest2.case.SkipTest
    except Exception:
        pass


class BaseTestCase(testtools.testcase.WithAttributes, testtools.TestCase):
    setUpClassCalled = False

    # NOTE(sdague): log_format is defined inline here instead of using the oslo
    # default because going through the config path recouples config to the
    # stress tests too early, and depending on testr order will fail unit tests
    log_format = ('%(asctime)s %(process)d %(levelname)-8s '
                  '[%(name)s] %(message)s')

    @classmethod
    def setUpClass(cls):
        if hasattr(super(BaseTestCase, cls), 'setUpClass'):
            super(BaseTestCase, cls).setUpClass()
        cls.setUpClassCalled = True
        # TODO(gmann): cls.handle_skip_exception is really workaround for
        # testtools bug- https://github.com/testing-cabal/testtools/issues/272
        # stestr which is used by Tempest internally to run the test switch
        # the customize test runner(which use stdlib unittest) for >=py3.5
        # else testtools.run.- https://github.com/mtreinish/stestr/pull/265
        # These two test runner are not compatible due to skip exception
        # handling(due to unittest2). testtools.run treat unittestt.SkipTest
        # as error and stdlib unittest treat unittest2.case.SkipTest raised
        # by testtools.TestCase.skipException.
        # The below workaround can be removed once testtools fix issue# 272.
        cls.orig_skip_exception = testtools.TestCase.skipException
        _handle_skip_exception()

    @classmethod
    def tearDownClass(cls):
        if hasattr(super(BaseTestCase, cls), 'tearDownClass'):
            super(BaseTestCase, cls).tearDownClass()

    def setUp(self):
        testtools.TestCase.skipException = self.orig_skip_exception
        super(BaseTestCase, self).setUp()
        if not self.setUpClassCalled:
            raise RuntimeError("setUpClass does not calls the super's "
                               "setUpClass in {!r}".format(type(self)))
        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))
        if (os.environ.get('OS_LOG_CAPTURE') != 'False' and
                os.environ.get('OS_LOG_CAPTURE') != '0'):
            self.useFixture(fixtures.LoggerFixture(nuke_handlers=False,
                                                   format=self.log_format,
                                                   level=None))
