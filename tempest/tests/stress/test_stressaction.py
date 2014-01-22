# Copyright 2013 Deutsche Telekom AG
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

import tempest.stress.stressaction as stressaction
import tempest.test


class FakeStressAction(stressaction.StressAction):
    def __init__(self, manager, max_runs=None, stop_on_error=False):
        super(self.__class__, self).__init__(manager, max_runs, stop_on_error)
        self._run_called = False

    def run(self):
        self._run_called = True

    @property
    def run_called(self):
        return self._run_called


class FakeStressActionFailing(stressaction.StressAction):
    def run(self):
        raise Exception('FakeStressActionFailing raise exception')


class TestStressAction(tempest.test.BaseTestCase):
    def _bulid_stats_dict(self, runs=0, fails=0):
        return {'runs': runs, 'fails': fails}

    def testStressTestRun(self):
        stressAction = FakeStressAction(manager=None, max_runs=1)
        stats = self._bulid_stats_dict()
        stressAction.execute(stats)
        self.assertTrue(stressAction.run_called)
        self.assertEqual(stats['runs'], 1)
        self.assertEqual(stats['fails'], 0)

    def testStressMaxTestRuns(self):
        stressAction = FakeStressAction(manager=None, max_runs=500)
        stats = self._bulid_stats_dict(runs=499)
        stressAction.execute(stats)
        self.assertTrue(stressAction.run_called)
        self.assertEqual(stats['runs'], 500)
        self.assertEqual(stats['fails'], 0)

    def testStressTestRunWithException(self):
        stressAction = FakeStressActionFailing(manager=None, max_runs=1)
        stats = self._bulid_stats_dict()
        stressAction.execute(stats)
        self.assertEqual(stats['runs'], 1)
        self.assertEqual(stats['fails'], 1)
