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

from oslo_log import log as logging

from tempest.common import image as common_image
from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.image.v1 import images_client as images_v1_client

CONF = config.CONF
LOG = logging.getLogger(__name__)


# NOTE(afazekas): This function needs to know a token and a subject.
def wait_for_server_status(client, server_id, status, ready_wait=True,
                           extra_timeout=0, raise_on_error=True):
    """Waits for a server to reach a given status."""

    def _get_task_state(body):
        return body.get('OS-EXT-STS:task_state', None)

    # NOTE(afazekas): UNKNOWN status possible on ERROR
    # or in a very early stage.
    body = client.show_server(server_id)['server']
    old_status = server_status = body['status']
    old_task_state = task_state = _get_task_state(body)
    start_time = int(time.time())
    timeout = client.build_timeout + extra_timeout
    while True:
        # NOTE(afazekas): Now the BUILD status only reached
        # between the UNKNOWN->ACTIVE transition.
        # TODO(afazekas): enumerate and validate the stable status set
        if status == 'BUILD' and server_status != 'UNKNOWN':
            return
        if server_status == status:
            if ready_wait:
                if status == 'BUILD':
                    return
                # NOTE(afazekas): The instance is in "ready for action state"
                # when no task in progress
                # NOTE(afazekas): Converted to string because of the XML
                # responses
                if str(task_state) == "None":
                    # without state api extension 3 sec usually enough
                    time.sleep(CONF.compute.ready_wait)
                    return
            else:
                return

        time.sleep(client.build_interval)
        body = client.show_server(server_id)['server']
        server_status = body['status']
        task_state = _get_task_state(body)
        if (server_status != old_status) or (task_state != old_task_state):
            LOG.info('State transition "%s" ==> "%s" after %d second wait',
                     '/'.join((old_status, str(old_task_state))),
                     '/'.join((server_status, str(task_state))),
                     time.time() - start_time)
        if (server_status == 'ERROR') and raise_on_error:
            if 'fault' in body:
                raise exceptions.BuildErrorException(body['fault'],
                                                     server_id=server_id)
            else:
                raise exceptions.BuildErrorException(server_id=server_id)

        timed_out = int(time.time()) - start_time >= timeout

        if timed_out:
            expected_task_state = 'None' if ready_wait else 'n/a'
            message = ('Server %(server_id)s failed to reach %(status)s '
                       'status and task state "%(expected_task_state)s" '
                       'within the required time (%(timeout)s s).' %
                       {'server_id': server_id,
                        'status': status,
                        'expected_task_state': expected_task_state,
                        'timeout': timeout})
            message += ' Current status: %s.' % server_status
            message += ' Current task state: %s.' % task_state
            caller = test_utils.find_test_caller()
            if caller:
                message = '(%s) %s' % (caller, message)
            raise exceptions.TimeoutException(message)
        old_status = server_status
        old_task_state = task_state


def wait_for_server_termination(client, server_id, ignore_error=False):
    """Waits for server to reach termination."""
    start_time = int(time.time())
    while True:
        try:
            body = client.show_server(server_id)['server']
        except lib_exc.NotFound:
            return

        server_status = body['status']
        if server_status == 'ERROR' and not ignore_error:
            raise exceptions.BuildErrorException(server_id=server_id)

        if int(time.time()) - start_time >= client.build_timeout:
            raise exceptions.TimeoutException

        time.sleep(client.build_interval)


def wait_for_image_status(client, image_id, status):
    """Waits for an image to reach a given status.

    The client should have a show_image(image_id) method to get the image.
    The client should also have build_interval and build_timeout attributes.
    """
    if isinstance(client, images_v1_client.ImagesClient):
        # The 'check_image' method is used here because the show_image method
        # returns image details plus the image itself which is very expensive.
        # The 'check_image' method returns just image details.
        def _show_image_v1(image_id):
            resp = client.check_image(image_id)
            return common_image.get_image_meta_from_headers(resp)

        show_image = _show_image_v1
    else:
        show_image = client.show_image

    current_status = 'An unknown status'
    start = int(time.time())
    while int(time.time()) - start < client.build_timeout:
        image = show_image(image_id)
        # Compute image client returns response wrapped in 'image' element
        # which is not case with Glance image client.
        if 'image' in image:
            image = image['image']

        current_status = image['status']
        if current_status == status:
            return
        if current_status.lower() == 'killed':
            raise exceptions.ImageKilledException(image_id=image_id,
                                                  status=status)
        if current_status.lower() == 'error':
            raise exceptions.AddImageException(image_id=image_id)

        time.sleep(client.build_interval)

    message = ('Image %(image_id)s failed to reach %(status)s state '
               '(current state %(current_status)s) within the required '
               'time (%(timeout)s s).' % {'image_id': image_id,
                                          'status': status,
                                          'current_status': current_status,
                                          'timeout': client.build_timeout})
    caller = test_utils.find_test_caller()
    if caller:
        message = '(%s) %s' % (caller, message)
    raise exceptions.TimeoutException(message)


def wait_for_volume_status(client, volume_id, status):
    """Waits for a Volume to reach a given status."""
    body = client.show_volume(volume_id)['volume']
    volume_status = body['status']
    start = int(time.time())

    while volume_status != status:
        time.sleep(client.build_interval)
        body = client.show_volume(volume_id)['volume']
        volume_status = body['status']
        if volume_status == 'error':
            raise exceptions.VolumeBuildErrorException(volume_id=volume_id)
        if volume_status == 'error_restoring':
            raise exceptions.VolumeRestoreErrorException(volume_id=volume_id)

        if int(time.time()) - start >= client.build_timeout:
            message = ('Volume %s failed to reach %s status (current %s) '
                       'within the required time (%s s).' %
                       (volume_id, status, volume_status,
                        client.build_timeout))
            raise exceptions.TimeoutException(message)


def wait_for_snapshot_status(client, snapshot_id, status):
    """Waits for a Snapshot to reach a given status."""
    body = client.show_snapshot(snapshot_id)['snapshot']
    snapshot_status = body['status']
    start = int(time.time())

    while snapshot_status != status:
        time.sleep(client.build_interval)
        body = client.show_snapshot(snapshot_id)['snapshot']
        snapshot_status = body['status']
        if snapshot_status == 'error':
            raise exceptions.SnapshotBuildErrorException(
                snapshot_id=snapshot_id)
        if int(time.time()) - start >= client.build_timeout:
            message = ('Snapshot %s failed to reach %s status (current %s) '
                       'within the required time (%s s).' %
                       (snapshot_id, status, snapshot_status,
                        client.build_timeout))
            raise exceptions.TimeoutException(message)


def wait_for_bm_node_status(client, node_id, attr, status):
    """Waits for a baremetal node attribute to reach given status.

    The client should have a show_node(node_uuid) method to get the node.
    """
    _, node = client.show_node(node_id)
    start = int(time.time())

    while node[attr] != status:
        time.sleep(client.build_interval)
        _, node = client.show_node(node_id)
        status_curr = node[attr]
        if status_curr == status:
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Node %(node_id)s failed to reach %(attr)s=%(status)s '
                       'within the required time (%(timeout)s s).' %
                       {'node_id': node_id,
                        'attr': attr,
                        'status': status,
                        'timeout': client.build_timeout})
            message += ' Current state of %s: %s.' % (attr, status_curr)
            caller = test_utils.find_test_caller()
            if caller:
                message = '(%s) %s' % (caller, message)
            raise exceptions.TimeoutException(message)
