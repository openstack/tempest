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
"""Describe follow-up actions using `PendingAction` class to verify
that nova API calls such as create/delete are completed"""


import logging
import time
from tempest.exceptions import TimeoutException


class PendingAction(object):
    """
    Initialize and describe actions to verify that a Nova API call
    is successful.
    """

    def __init__(self, nova_manager, timeout=None):
        """
        `nova_manager` : Manager object.
        `timeout`   : time before we declare a TimeoutException
        """
        if timeout is None:
            timeout = nova_manager.config.compute.build_timeout
        self._manager = nova_manager
        self._logger = logging.getLogger(self.__class__.__name__)
        self._start_time = time.time()
        self._timeout = timeout

    def retry(self):
        """
        Invoked by user of this class to verify completion of
        previous TestCase actions
        """
        return False

    def check_timeout(self):
        """Check for timeouts of TestCase actions"""
        time_diff = time.time() - self._start_time
        if time_diff > self._timeout:
            self._logger.error('%s exceeded timeout of %d' %
                               (self.__class__.__name__, self._timeout))
            raise TimeoutException

    def elapsed(self):
        return time.time() - self._start_time


class PendingServerAction(PendingAction):
    """
    Initialize and describe actions to verify that a Nova API call that
    changes server state is successful.
    """

    def __init__(self, nova_manager, state, target_server, timeout=None):
        """
        `state`           : externally maintained data structure about
                            state of VMs or other persistent objects in
                            the nova cluster
        `target_server`   : server that actions were performed on
        """
        super(PendingServerAction, self).__init__(nova_manager,
                                                  timeout=timeout)
        self._state = state
        self._target = target_server

    def _check_for_status(self, state_string):
        """Check to see if the machine has transitioned states"""
        t = time.time()  # for debugging
        target = self._target
        _resp, body = self._manager.servers_client.get_server(target['id'])
        if body['status'] != state_string:
            # grab the actual state as we think it is
            temp_obj = self._state.get_instances()[target['id']]
            self._logger.debug("machine %s in state %s" %
                               (target['id'], temp_obj[1]))
            self._logger.debug('%s, time: %d' % (temp_obj[1], time.time() - t))
            return temp_obj[1]
        self._logger.debug('%s, time: %d' % (state_string, time.time() - t))
        return state_string
