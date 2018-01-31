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

import time

import testtools

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesExtendTest(base.BaseVolumeTest):

    @decorators.idempotent_id('9a36df71-a257-43a5-9555-dc7c88e66e0e')
    def test_volume_extend(self):
        # Extend Volume Test.
        volume = self.create_volume()
        extend_size = volume['size'] + 1
        self.volumes_client.extend_volume(volume['id'],
                                          new_size=extend_size)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        volume = self.volumes_client.show_volume(volume['id'])['volume']
        self.assertEqual(volume['size'], extend_size)

    @decorators.idempotent_id('86be1cba-2640-11e5-9c82-635fb964c912')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          "Cinder volume snapshots are disabled")
    @decorators.skip_because(bug='1687044')
    def test_volume_extend_when_volume_has_snapshot(self):
        volume = self.create_volume()
        self.create_snapshot(volume['id'])

        extend_size = volume['size'] + 1
        self.volumes_client.extend_volume(volume['id'], new_size=extend_size)

        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        resized_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(extend_size, resized_volume['size'])


class VolumesExtendAttachedTest(base.BaseVolumeTest):
    """Tests extending the size of an attached volume."""

    # We need admin credentials for getting instance action event details. By
    # default a non-admin can list and show instance actions if they own the
    # server instance, but since the event details can contain error messages
    # and tracebacks, like an instance fault, those are not viewable by
    # non-admins. This is obviously not a great user experience since the user
    # may not know when the operation is actually complete. A microversion in
    # the compute API will be added so that non-admins can see instance action
    # events but will continue to hide the traceback field.
    # TODO(mriedem): Change this to not rely on the admin user to get the event
    # details once that microversion is available in Nova.
    credentials = ['primary', 'admin']

    _api_version = 3
    # NOTE(mriedem): The minimum required volume API version is 3.42 and the
    # minimum required compute API microversion is 2.51, but the compute call
    # is implicit - Cinder calls Nova at that microversion, Tempest does not.
    min_microversion = '3.42'

    def _find_extend_volume_instance_action(self, server_id):
        actions = self.servers_client.list_instance_actions(
            server_id)['instanceActions']
        for action in actions:
            if action['action'] == 'extend_volume':
                return action

    def _find_extend_volume_instance_action_finish_event(self, action):
        # This has to be called by an admin client otherwise
        # the events don't show up.
        action = self.os_admin.servers_client.show_instance_action(
            action['instance_uuid'], action['request_id'])['instanceAction']
        for event in action['events']:
            if (event['event'] == 'compute_extend_volume' and
                    event['finish_time']):
                return event

    @decorators.idempotent_id('301f5a30-1c6f-4ea0-be1a-91fd28d44354')
    @testtools.skipUnless(CONF.volume_feature_enabled.extend_attached_volume,
                          "Attached volume extend is disabled.")
    @utils.services('compute')
    def test_extend_attached_volume(self):
        """This is a happy path test which does the following:

        * Create a volume at the configured volume_size.
        * Create a server instance.
        * Attach the volume to the server.
        * Wait for the volume status to be "in-use".
        * Extend the size of the volume and wait for the volume status to go
          back to "in-use".
        * Assert the volume size change is reflected in the volume API.
        * Wait for the "compute_extend_volume" instance action event to show
          up in the compute API with the success or failure status. We fail
          if we timeout waiting for the instance action event to show up, or
          if the action on the server fails.
        """
        # Create a test volume. Will be automatically cleaned up on teardown.
        volume = self.create_volume()
        # Create a test server. Will be automatically cleaned up on teardown.
        server = self.create_server()
        # Attach the volume to the server and wait for the volume status to be
        # "in-use".
        self.attach_volume(server['id'], volume['id'])
        # Extend the size of the volume. If this is successful, the volume API
        # will change the status on the volume to "extending" before doing an
        # RPC cast to the volume manager on the backend. Note that we multiply
        # the size of the volume since certain Cinder backends, e.g. ScaleIO,
        # require multiples of 8GB.
        extend_size = volume['size'] * 2
        self.volumes_client.extend_volume(volume['id'], new_size=extend_size)
        # The volume status should go back to in-use since it is still attached
        # to the server instance.
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'in-use')
        # Assert that the volume size has changed in the volume API.
        volume = self.volumes_client.show_volume(volume['id'])['volume']
        self.assertEqual(extend_size, volume['size'])
        # Now we wait for the "compute_extend_volume" instance action event
        # to show up for the server instance. This is our indication that the
        # asynchronous operation is complete on the compute side.
        start_time = int(time.time())
        timeout = self.servers_client.build_timeout
        action = self._find_extend_volume_instance_action(server['id'])
        while action is None and int(time.time()) - start_time < timeout:
            time.sleep(self.servers_client.build_interval)
            action = self._find_extend_volume_instance_action(server['id'])

        if action is None:
            msg = ("Timed out waiting to get 'extend_volume' instance action "
                   "record for server %(server)s after %(timeout)s seconds." %
                   {'server': server['id'], 'timeout': timeout})
            raise lib_exc.TimeoutException(msg)

        # Now that we found the extend_volume instance action, we can wait for
        # the compute_extend_volume instance action event to show up to
        # indicate the operation is complete.
        start_time = int(time.time())
        event = self._find_extend_volume_instance_action_finish_event(action)
        while event is None and int(time.time()) - start_time < timeout:
            time.sleep(self.servers_client.build_interval)
            event = self._find_extend_volume_instance_action_finish_event(
                action)

        if event is None:
            msg = ("Timed out waiting to get 'compute_extend_volume' instance "
                   "action event record for server %(server)s and request "
                   "%(request_id)s after %(timeout)s seconds." %
                   {'server': server['id'],
                    'request_id': action['request_id'],
                    'timeout': timeout})
            raise lib_exc.TimeoutException(msg)

        # Finally, assert that the action completed successfully.
        self.assertTrue(
            event['result'].lower() == 'success',
            "Unexpected compute_extend_volume result '%(result)s' for request "
            "%(request_id)s." %
            {'result': event['result'],
             'request_id': action['request_id']})
