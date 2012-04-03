# Copyright 2011 Quanta Research Cambridge, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""Class to describe actions to be included in a stress test."""


class BasherAction(object):
    """
    Used to describe each action that you would like to include in a test run.
    """

    def __init__(self, test_case, probability, pargs=[], kargs={}):
        """
        `test_case`  : the name of the class that implements the action
        `pargs`      : positional arguments to the constructor of `test_case`
        `kargs`      : keyword arguments to the constructor of `test_case`
        `probability`: frequency that each action
        """
        self.test_case = test_case
        self.pargs = pargs
        self.kargs = kargs
        self.probability = probability

    def invoke(self, manager, state):
        """
        Calls the `run` method of the `test_case`.
        """
        return self.test_case.run(manager, state, *self.pargs, **self.kargs)

    def __str__(self):
        return self.test_case.__class__.__name__
