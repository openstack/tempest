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

import re
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


def _get_task_state(body):
    return body.get('OS-EXT-STS:task_state', None)


# NOTE(afazekas): This function needs to know a token and a subject.
def wait_for_server_status(client, server_id, status, ready_wait=True,
                           extra_timeout=0, raise_on_error=True):
    """Waits for a server to reach a given status."""

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
                if task_state is None:
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
            raise lib_exc.TimeoutException(message)
        old_status = server_status
        old_task_state = task_state


def wait_for_server_termination(client, server_id, ignore_error=False):
    """Waits for server to reach termination."""
    try:
        body = client.show_server(server_id)['server']
    except lib_exc.NotFound:
        return
    old_status = body['status']
    old_task_state = _get_task_state(body)
    start_time = int(time.time())
    while True:
        time.sleep(client.build_interval)
        try:
            body = client.show_server(server_id)['server']
        except lib_exc.NotFound:
            return
        server_status = body['status']
        task_state = _get_task_state(body)
        if (server_status != old_status) or (task_state != old_task_state):
            LOG.info('State transition "%s" ==> "%s" after %d second wait',
                     '/'.join((old_status, str(old_task_state))),
                     '/'.join((server_status, str(task_state))),
                     time.time() - start_time)
        if server_status == 'ERROR' and not ignore_error:
            raise lib_exc.DeleteErrorException(
                "Server %s failed to delete and is in ERROR status" %
                server_id)

        if server_status == 'SOFT_DELETED':
            # Soft-deleted instances need to be forcibly deleted to
            # prevent some test cases from failing.
            LOG.debug("Automatically force-deleting soft-deleted server %s",
                      server_id)
            try:
                client.force_delete_server(server_id)
            except lib_exc.NotFound:
                # The instance may have been deleted so ignore
                # NotFound exception
                return

        if int(time.time()) - start_time >= client.build_timeout:
            raise lib_exc.TimeoutException
        old_status = server_status
        old_task_state = task_state


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
        # which is not the case with Glance image client.
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
    raise lib_exc.TimeoutException(message)


def wait_for_image_tasks_status(client, image_id, status):
    """Waits for an image tasks to reach a given status."""
    pending_tasks = []
    start = int(time.time())
    while int(time.time()) - start < client.build_timeout:
        tasks = client.show_image_tasks(image_id)['tasks']

        pending_tasks = [task for task in tasks if task['status'] != status]
        if not pending_tasks:
            return tasks
        time.sleep(client.build_interval)

    message = ('Image %(image_id)s tasks: %(pending_tasks)s '
               'failed to reach %(status)s state within the required '
               'time (%(timeout)s s).' % {'image_id': image_id,
                                          'pending_tasks': pending_tasks,
                                          'status': status,
                                          'timeout': client.build_timeout})
    caller = test_utils.find_test_caller()
    if caller:
        message = '(%s) %s' % (caller, message)
    raise lib_exc.TimeoutException(message)


def wait_for_image_imported_to_stores(client, image_id, stores=None):
    """Waits for an image to be imported to all requested stores.

    Short circuits to fail if the serer reports failure of any store.
    If stores is None, just wait for status==active.

    The client should also have build_interval and build_timeout attributes.
    """

    exc_cls = lib_exc.TimeoutException
    start = int(time.time())
    while int(time.time()) - start < client.build_timeout:
        image = client.show_image(image_id)
        if image['status'] == 'active' and (stores is None or
                                            image['stores'] == stores):
            return
        if image.get('os_glance_failed_import'):
            exc_cls = lib_exc.OtherRestClientException
            break

        time.sleep(client.build_interval)

    message = ('Image %s failed to import on stores: %s' %
               (image_id, str(image.get('os_glance_failed_import'))))
    caller = test_utils.find_test_caller()
    if caller:
        message = '(%s) %s' % (caller, message)
    raise exc_cls(message)


def wait_for_image_copied_to_stores(client, image_id):
    """Waits for an image to be copied on all requested stores.

    The client should also have build_interval and build_timeout attributes.
    This return the list of stores where copy is failed.
    """

    start = int(time.time())
    store_left = []
    while int(time.time()) - start < client.build_timeout:
        image = client.show_image(image_id)
        store_left = image.get('os_glance_importing_to_stores')
        # NOTE(danms): If os_glance_importing_to_stores is None, then
        # we've raced with the startup of the task and should continue
        # to wait.
        if store_left is not None and not store_left:
            return image['os_glance_failed_import']
        if image['status'].lower() == 'killed':
            raise exceptions.ImageKilledException(image_id=image_id,
                                                  status=image['status'])

        time.sleep(client.build_interval)

    message = ('Image %s failed to finish the copy operation '
               'on stores: %s' % (image_id, str(store_left)))
    caller = test_utils.find_test_caller()
    if caller:
        message = '(%s) %s' % (caller, message)
    raise lib_exc.TimeoutException(message)


def wait_for_volume_resource_status(client, resource_id, status):
    """Waits for a volume resource to reach a given status.

    This function is a common function for volume, snapshot and backup
    resources. The function extracts the name of the desired resource from
    the client class name of the resource.
    """
    resource_name = re.findall(
        r'(volume|group-snapshot|snapshot|backup|group)',
        client.resource_type)[-1].replace('-', '_')
    show_resource = getattr(client, 'show_' + resource_name)
    resource_status = show_resource(resource_id)[resource_name]['status']
    start = int(time.time())

    while resource_status != status:
        time.sleep(client.build_interval)
        resource_status = show_resource(resource_id)[
            '{}'.format(resource_name)]['status']
        if resource_status == 'error' and resource_status != status:
            raise exceptions.VolumeResourceBuildErrorException(
                resource_name=resource_name, resource_id=resource_id)
        if resource_name == 'volume' and resource_status == 'error_restoring':
            raise exceptions.VolumeRestoreErrorException(volume_id=resource_id)
        if resource_status == 'error_extending' and resource_status != status:
            raise exceptions.VolumeExtendErrorException(volume_id=resource_id)

        if int(time.time()) - start >= client.build_timeout:
            message = ('%s %s failed to reach %s status (current %s) '
                       'within the required time (%s s).' %
                       (resource_name, resource_id, status, resource_status,
                        client.build_timeout))
            raise lib_exc.TimeoutException(message)
    LOG.info('%s %s reached %s after waiting for %f seconds',
             resource_name, resource_id, status, time.time() - start)


def wait_for_volume_attachment_create(client, volume_id, server_id):
    """Waits for a volume attachment to be created at a given volume."""
    start = int(time.time())
    while True:
        attachments = client.show_volume(volume_id)['volume']['attachments']
        found = [a for a in attachments if a['server_id'] == server_id]
        if found:
            LOG.info('Attachment %s created for volume %s to server %s after '
                     'waiting for %f seconds', found[0]['attachment_id'],
                     volume_id, server_id, time.time() - start)
            return found[0]
        time.sleep(client.build_interval)
        if int(time.time()) - start >= client.build_timeout:
            message = ('Failed to attach volume %s to server %s '
                       'within the required time (%s s).' %
                       (volume_id, server_id, client.build_timeout))
            raise lib_exc.TimeoutException(message)


def wait_for_volume_attachment_remove(client, volume_id, attachment_id):
    """Waits for a volume attachment to be removed from a given volume."""
    start = int(time.time())
    attachments = client.show_volume(volume_id)['volume']['attachments']
    while any(attachment_id == a['attachment_id'] for a in attachments):
        time.sleep(client.build_interval)
        if int(time.time()) - start >= client.build_timeout:
            message = ('Failed to remove attachment %s from volume %s '
                       'within the required time (%s s).' %
                       (attachment_id, volume_id, client.build_timeout))
            raise lib_exc.TimeoutException(message)
        attachments = client.show_volume(volume_id)['volume']['attachments']
    LOG.info('Attachment %s removed from volume %s after waiting for %f '
             'seconds', attachment_id, volume_id, time.time() - start)


def wait_for_volume_attachment_remove_from_server(
        client, server_id, volume_id):
    """Waits for a volume to be removed from a given server.

    This waiter checks the compute API if the volume attachment is removed.
    """
    start = int(time.time())

    try:
        volumes = client.list_volume_attachments(
            server_id)['volumeAttachments']
    except lib_exc.NotFound:
        # Ignore 404s on detach in case the server is deleted or the volume
        # is already detached.
        return

    while any(volume for volume in volumes if volume['volumeId'] == volume_id):
        time.sleep(client.build_interval)

        timed_out = int(time.time()) - start >= client.build_timeout
        if timed_out:
            console_output = client.get_console_output(server_id)['output']
            LOG.debug('Console output for %s\nbody=\n%s',
                      server_id, console_output)
            message = ('Volume %s failed to detach from server %s within '
                       'the required time (%s s) from the compute API '
                       'perspective' %
                       (volume_id, server_id, client.build_timeout))
            raise lib_exc.TimeoutException(message)
        try:
            volumes = client.list_volume_attachments(
                server_id)['volumeAttachments']
        except lib_exc.NotFound:
            # Ignore 404s on detach in case the server is deleted or the volume
            # is already detached.
            return
    return


def wait_for_volume_migration(client, volume_id, new_host):
    """Waits for a Volume to move to a new host."""
    body = client.show_volume(volume_id)['volume']
    host = body['os-vol-host-attr:host']
    migration_status = body['migration_status']
    start = int(time.time())

    # new_host is hostname@backend while current_host is hostname@backend#type
    while migration_status != 'success' or new_host not in host:
        time.sleep(client.build_interval)
        body = client.show_volume(volume_id)['volume']
        host = body['os-vol-host-attr:host']
        migration_status = body['migration_status']

        if migration_status == 'error':
            message = ('volume %s failed to migrate.' % (volume_id))
            raise lib_exc.TempestException(message)

        if int(time.time()) - start >= client.build_timeout:
            message = ('Volume %s failed to migrate to %s (current %s) '
                       'within the required time (%s s).' %
                       (volume_id, new_host, host, client.build_timeout))
            raise lib_exc.TimeoutException(message)


def wait_for_volume_retype(client, volume_id, new_volume_type):
    """Waits for a Volume to have a new volume type."""
    body = client.show_volume(volume_id)['volume']
    current_volume_type = body['volume_type']
    start = int(time.time())

    while current_volume_type != new_volume_type:
        time.sleep(client.build_interval)
        body = client.show_volume(volume_id)['volume']
        current_volume_type = body['volume_type']

        if int(time.time()) - start >= client.build_timeout:
            message = ('Volume %s failed to reach %s volume type (current %s) '
                       'within the required time (%s s).' %
                       (volume_id, new_volume_type, current_volume_type,
                        client.build_timeout))
            raise lib_exc.TimeoutException(message)


def wait_for_qos_operations(client, qos_id, operation, args=None):
    """Waits for a qos operations to be completed.

    NOTE : operation value is required for  wait_for_qos_operations()
    operation = 'qos-key' / 'disassociate' / 'disassociate-all'
    args = keys[] when operation = 'qos-key'
    args = volume-type-id disassociated when operation = 'disassociate'
    args = None when operation = 'disassociate-all'
    """
    start_time = int(time.time())
    while True:
        if operation == 'qos-key-unset':
            body = client.show_qos(qos_id)['qos_specs']
            if not any(key in body['specs'] for key in args):
                return
        elif operation == 'disassociate':
            body = client.show_association_qos(qos_id)['qos_associations']
            if not any(args in body[i]['id'] for i in range(0, len(body))):
                return
        elif operation == 'disassociate-all':
            body = client.show_association_qos(qos_id)['qos_associations']
            if not body:
                return
        else:
            msg = (" operation value is either not defined or incorrect.")
            raise lib_exc.UnprocessableEntity(msg)

        if int(time.time()) - start_time >= client.build_timeout:
            raise lib_exc.TimeoutException
        time.sleep(client.build_interval)


def wait_for_interface_status(client, server_id, port_id, status):
    """Waits for an interface to reach a given status."""
    body = (client.show_interface(server_id, port_id)
            ['interfaceAttachment'])
    interface_status = body['port_state']
    start = int(time.time())

    while(interface_status != status):
        time.sleep(client.build_interval)
        body = (client.show_interface(server_id, port_id)
                ['interfaceAttachment'])
        interface_status = body['port_state']

        timed_out = int(time.time()) - start >= client.build_timeout

        if interface_status != status and timed_out:
            message = ('Interface %s failed to reach %s status '
                       '(current %s) within the required time (%s s).' %
                       (port_id, status, interface_status,
                        client.build_timeout))
            raise lib_exc.TimeoutException(message)

    return body


def wait_for_interface_detach(client, server_id, port_id):
    """Waits for an interface to be detached from a server."""
    body = client.list_interfaces(server_id)['interfaceAttachments']
    ports = [iface['port_id'] for iface in body]
    start = int(time.time())

    while port_id in ports:
        time.sleep(client.build_interval)
        body = client.list_interfaces(server_id)['interfaceAttachments']
        ports = [iface['port_id'] for iface in body]
        if port_id not in ports:
            return body

        timed_out = int(time.time()) - start >= client.build_timeout
        if timed_out:
            message = ('Interface %s failed to detach from server %s within '
                       'the required time (%s s)' % (port_id, server_id,
                                                     client.build_timeout))
            raise lib_exc.TimeoutException(message)


def wait_for_guest_os_boot(client, server_id):
    start_time = int(time.time())
    while True:
        console_output = client.get_console_output(server_id)['output']
        for line in console_output.split('\n'):
            if 'login:' in line.lower():
                return
        if int(time.time()) - start_time >= client.build_timeout:
            LOG.info("Guest OS on server %s probably isn't ready or its "
                     "console log can't be parsed properly. If guest OS "
                     "isn't ready, that may cause problems with SSH to "
                     "the server.",
                     server_id)
            return
        time.sleep(client.build_interval)
