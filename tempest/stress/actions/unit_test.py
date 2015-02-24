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

from oslo_log import log as logging
from oslo_utils import importutils

from tempest import config
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class SetUpClassRunTime(object):

    process = 'process'
    action = 'action'
    application = 'application'

    allowed = set((process, action, application))

    @classmethod
    def validate(cls, name):
        if name not in cls.allowed:
            raise KeyError("\'%s\' not a valid option" % name)


class UnitTest(stressaction.StressAction):
    """This is a special action for running existing unittests as stress test.
       You need to pass ``test_method`` and ``class_setup_per``
       using ``kwargs`` in the JSON descriptor;
       ``test_method`` should be the fully qualified name of a unittest,
       ``class_setup_per`` should be one from:
           ``application``: once in the stress job lifetime
           ``process``: once in the worker process lifetime
           ``action``: on each action
       Not all combination working in every case.
    """

    def setUp(self, **kwargs):
        method = kwargs['test_method'].split('.')
        self.test_method = method.pop()
        self.klass = importutils.import_class('.'.join(method))
        self.logger = logging.getLogger('.'.join(method))
        # valid options are 'process', 'application' , 'action'
        self.class_setup_per = kwargs.get('class_setup_per',
                                          SetUpClassRunTime.process)
        SetUpClassRunTime.validate(self.class_setup_per)

        if self.class_setup_per == SetUpClassRunTime.application:
            self.klass.setUpClass()
        self.setupclass_called = False

    @property
    def action(self):
        if self.test_method:
            return self.test_method
        return super(UnitTest, self).action

    def run_core(self):
        res = self.klass(self.test_method).run()
        if res.errors:
            raise RuntimeError(res.errors)

    def run(self):
        if self.class_setup_per != SetUpClassRunTime.application:
            if (self.class_setup_per == SetUpClassRunTime.action
                or self.setupclass_called is False):
                self.klass.setUpClass()
                self.setupclass_called = True

            try:
                self.run_core()
            except Exception as e:
                raise e
            finally:
                if (CONF.stress.leave_dirty_stack is False
                    and self.class_setup_per == SetUpClassRunTime.action):
                    self.klass.tearDownClass()
        else:
            self.run_core()

    def tearDown(self):
        if self.class_setup_per != SetUpClassRunTime.action:
            self.klass.tearDownClass()
