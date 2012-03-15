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
"""Abstract class for implementing an action. You only need to override
the `run` method which specifies all the actual nova API class you wish
to make."""


import logging


class StressTestCase(object):

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def run(self, nova_manager, state_obj, *pargs, **kargs):
        """Nova API methods to call that would modify state of the cluster"""
        return
