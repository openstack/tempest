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


class PendingAction(object):
    """
    Initialize and describe actions to verify that a Nova API call
    is successful.
    """

    def __init__(self, nova_manager, state, target_server, timeout=600):
        """
        `nova_manager` : Manager object.
        `state`           : externally maintained data structure about
                            state of VMs or other persistent objects in
                            the nova cluster
        `target_server`   : server that actions were performed on
        `target_server`   : time before we declare a TimeoutException
        `pargs`           : positional arguments
        `kargs`           : keyword arguments
        """
        self._manager = nova_manager
        self._state = state
        self._target = target_server

        self._logger = logging.getLogger(self.__class__.__name__)
        self._start_time = time.time()
        self._timeout = timeout

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

    def retry(self):
        """Invoked by user of this class to verify completion of"""
        """previous TestCase actions"""
        return False
