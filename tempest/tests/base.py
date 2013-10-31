# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import os

import fixtures
import mox
import stubout
import testtools


class MoxStubout(fixtures.Fixture):
    """Deal with code around mox and stubout as a fixture."""

    def setUp(self):
        super(MoxStubout, self).setUp()
        # emulate some of the mox stuff, we can't use the metaclass
        # because it screws with our generators
        self.mox = mox.Mox()
        self.stubs = stubout.StubOutForTesting()
        self.addCleanup(self.stubs.UnsetAll)
        self.addCleanup(self.stubs.SmartUnsetAll)
        self.addCleanup(self.mox.UnsetStubs)
        self.addCleanup(self.mox.VerifyAll)


class TestCase(testtools.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        mox_fixture = self.useFixture(MoxStubout())
        self.mox = mox_fixture.mox
        self.stubs = mox_fixture.stubs
