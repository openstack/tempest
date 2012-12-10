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
"""Defines various sub-classes of the `StressTestCase` and
`PendingServerAction` class. Sub-classes of StressTestCase implement various
API calls on the Nova cluster having to do with creating and deleting VMs.
Each sub-class will have a corresponding PendingServerAction. These pending
actions veriy that the API call was successful or not."""

import random
import time

import pending_action
import test_case


class TestCreateVM(test_case.StressTestCase):
    """Create a virtual machine in the Nova cluster."""
    _vm_id = 0

    def run(self, manager, state, *pargs, **kwargs):
        """
        Send an HTTP POST request to the nova cluster to build a
        server. Update the state variable to track state of new server
        and set to PENDING state.

        `manager` : Manager object.
        `state`      : `State` object describing our view of state of cluster
        `pargs`      : positional arguments
        `kwargs`     : keyword arguments, which include:
                       `key_name`  : name of keypair
                       `timeout`   : how long to wait before issuing Exception
                       `image_ref` : index to image types availablexs
                       `flavor_ref`: index to flavor types available
                                     (default = 1, which is tiny)
        """

        # restrict number of instances we can launch
        if len(state.get_instances()) >= state.get_max_instances():
            self._logger.debug("maximum number of instances created: %d" %
                               state.get_max_instances())
            return None

        _key_name = kwargs.get('key_name', '')
        _timeout = int(kwargs.get('timeout',
                                  manager.config.compute.build_timeout))
        _image_ref = kwargs.get('image_ref', manager.config.compute.image_ref)
        _flavor_ref = kwargs.get('flavor_ref',
                                 manager.config.compute.flavor_ref)

        expected_server = {
            'name': 'server' + str(TestCreateVM._vm_id),
            'metadata': {
                'key1': 'value1',
                'key2': 'value2',
            },
            'imageRef': _image_ref,
            'flavorRef': _flavor_ref,
            'adminPass': 'testpwd',
            'key_name': _key_name,
        }
        TestCreateVM._vm_id = TestCreateVM._vm_id + 1
        create_server = manager.servers_client.create_server
        response, body = create_server(expected_server['name'],
                                       _image_ref,
                                       _flavor_ref,
                                       meta=expected_server['metadata'],
                                       adminPass=expected_server['adminPass'])

        if (response.status != 202):
            self._logger.error("response: %s" % response)
            self._logger.error("body: %s" % body)
            raise Exception

        created_server = body

        self._logger.info('setting machine %s to BUILD' %
                          created_server['id'])
        state.set_instance_state(created_server['id'],
                                (created_server, 'BUILD'))

        return VerifyCreateVM(manager,
                              state,
                              created_server,
                              expected_server)


class VerifyCreateVM(pending_action.PendingServerAction):
    """Verify that VM was built and is running"""
    def __init__(self, manager,
                 state,
                 created_server,
                 expected_server):
        super(VerifyCreateVM, self).__init__(manager,
                                             state,
                                             created_server,
                                             )
        self._expected = expected_server

    def retry(self):
        """
        Check to see that the server was created and is running.
        Update local view of state to indicate that it is running.
        """
        # don't run create verification
        # if target machine has been deleted or is going to be deleted
        target_id = self._target['id']
        if (self._target['id'] not in self._state.get_instances().keys() or
            self._state.get_instances()[target_id][1] == 'TERMINATING'):
            self._logger.info('machine %s is deleted or TERMINATING' %
                              self._target['id'])
            return True

        admin_pass = self._target['adminPass']
        # Could check more things here.
        if (self._expected['adminPass'] != admin_pass):
            self._logger.error('expected: %s' %
                               (self._expected['adminPass']))
            self._logger.error('returned: %s' %
                               (admin_pass))
            raise Exception

        if self._check_for_status('ACTIVE') != 'ACTIVE':
            return False

        self._logger.info('machine %s: BUILD -> ACTIVE [%.1f secs elapsed]' %
                          (self._target['id'], self.elapsed()))
        self._state.set_instance_state(self._target['id'],
                                      (self._target, 'ACTIVE'))
        return True


class TestKillActiveVM(test_case.StressTestCase):
    """Class to destroy a random ACTIVE server."""
    def run(self, manager, state, *pargs, **kwargs):
        """
        Send an HTTP POST request to the nova cluster to destroy
        a random ACTIVE server. Update `state` to indicate TERMINATING.

        `manager` : Manager object.
        `state`      : `State` object describing our view of state of cluster
        `pargs`      : positional arguments
        `kwargs`     : keyword arguments, which include:
                       `timeout` : how long to wait before issuing Exception
        """
        # check for active instances
        vms = state.get_instances()
        active_vms = [v for k, v in vms.iteritems() if v and v[1] == 'ACTIVE']
        # no active vms, so return null
        if not active_vms:
            self._logger.info('no ACTIVE instances to delete')
            return

        _timeout = kwargs.get('timeout', manager.config.compute.build_timeout)

        target = random.choice(active_vms)
        killtarget = target[0]
        manager.servers_client.delete_server(killtarget['id'])
        self._logger.info('machine %s: ACTIVE -> TERMINATING' %
                          killtarget['id'])
        state.set_instance_state(killtarget['id'],
                                (killtarget, 'TERMINATING'))
        return VerifyKillActiveVM(manager, state,
                                  killtarget, timeout=_timeout)


class VerifyKillActiveVM(pending_action.PendingServerAction):
    """Verify that server was destroyed"""

    def retry(self):
        """
        Check to see that the server of interest is destroyed. Update
        state to indicate that server is destroyed by deleting it from local
        view of state.
        """
        tid = self._target['id']
        # if target machine has been deleted from the state, then it was
        # already verified to be deleted
        if (not tid in self._state.get_instances().keys()):
            return False

        try:
            self._manager.servers_client.get_server(tid)
        except Exception:
            # if we get a 404 response, is the machine really gone?
            target = self._target
            self._logger.info('machine %s: DELETED [%.1f secs elapsed]' %
                              (target['id'], self.elapsed()))
            self._state.delete_instance_state(target['id'])
            return True

        return False


class TestKillAnyVM(test_case.StressTestCase):
    """Class to destroy a random server regardless of state."""

    def run(self, manager, state, *pargs, **kwargs):
        """
        Send an HTTP POST request to the nova cluster to destroy
        a random server. Update state to TERMINATING.

        `manager` : Manager object.
        `state`      : `State` object describing our view of state of cluster
        `pargs`      : positional arguments
        `kwargs`     : keyword arguments, which include:
                       `timeout` : how long to wait before issuing Exception
        """

        vms = state.get_instances()
        # no vms, so return null
        if not vms:
            self._logger.info('no active instances to delete')
            return

        _timeout = kwargs.get('timeout', manager.config.compute.build_timeout)

        target = random.choice(vms)
        killtarget = target[0]

        manager.servers_client.delete_server(killtarget['id'])
        self._state.set_instance_state(killtarget['id'],
                                      (killtarget, 'TERMINATING'))
        # verify object will do the same thing as the active VM
        return VerifyKillAnyVM(manager, state, killtarget, timeout=_timeout)

VerifyKillAnyVM = VerifyKillActiveVM


class TestUpdateVMName(test_case.StressTestCase):
    """Class to change the name of the active server"""
    def run(self, manager, state, *pargs, **kwargs):
        """
        Issue HTTP POST request to change the name of active server.
        Update state of server to reflect name changing.

        `manager` : Manager object.
        `state`      : `State` object describing our view of state of cluster
        `pargs`      : positional arguments
        `kwargs`     : keyword arguments, which include:
                       `timeout`   : how long to wait before issuing Exception
        """

        # select one machine from active ones
        vms = state.get_instances()
        active_vms = [v for k, v in vms.iteritems() if v and v[1] == 'ACTIVE']
        # no active vms, so return null
        if not active_vms:
            self._logger.info('no active instances to update')
            return

        _timeout = kwargs.get('timeout', manager.config.compute.build_timeout)

        target = random.choice(active_vms)
        update_target = target[0]

        # Update name by appending '_updated' to the name
        new_name = update_target['name'] + '_updated'
        (response, body) = \
            manager.servers_client.update_server(update_target['id'],
                                                 name=new_name)
        if (response.status != 200):
            self._logger.error("response: %s " % response)
            self._logger.error("body: %s " % body)
            raise Exception

        assert(new_name == body['name'])

        self._logger.info('machine %s: ACTIVE -> UPDATING_NAME' %
                          body['id'])
        state.set_instance_state(body['id'],
                                (body, 'UPDATING_NAME'))

        return VerifyUpdateVMName(manager,
                                  state,
                                  body,
                                  timeout=_timeout)


class VerifyUpdateVMName(pending_action.PendingServerAction):
    """Check that VM has new name"""
    def retry(self):
        """
        Check that VM has new name. Update local view of `state` to RUNNING.
        """
        # don't run update verification
        # if target machine has been deleted or is going to be deleted
        target_id = self._target['id']
        if (not self._target['id'] in self._state.get_instances().keys() or
            self._state.get_instances()[target_id][1] == 'TERMINATING'):
            return False

        response, body = \
            self._manager.serverse_client.get_server(self._target['id'])
        if (response.status != 200):
            self._logger.error("response: %s " % response)
            self._logger.error("body: %s " % body)
            raise Exception

        if self._target['name'] != body['name']:
            self._logger.error(self._target['name'] +
                               ' vs. ' +
                               body['name'])
            raise Exception

        # log the update
        self._logger.info('machine %s: UPDATING_NAME -> ACTIVE' %
                          self._target['id'])
        self._state.set_instance_state(self._target['id'],
                                      (body,
                                       'ACTIVE'))
        return True
