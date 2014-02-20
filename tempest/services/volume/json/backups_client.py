# Copyright 2014 OpenStack Foundation
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

import json
import time

from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class BackupsClientJSON(rest_client.RestClient):
    """
    Client class to send CRUD Volume backup API requests to a Cinder endpoint
    """

    def __init__(self, auth_provider):
        super(BackupsClientJSON, self).__init__(auth_provider)
        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.volume.build_interval
        self.build_timeout = CONF.volume.build_timeout

    def create_backup(self, volume_id, container=None, name=None,
                      description=None):
        """Creates a backup of volume."""
        post_body = {'volume_id': volume_id}
        if container:
            post_body['container'] = container
        if name:
            post_body['name'] = name
        if description:
            post_body['description'] = description
        post_body = json.dumps({'backup': post_body})
        resp, body = self.post('backups', post_body)
        body = json.loads(body)
        return resp, body['backup']

    def restore_backup(self, backup_id, volume_id=None):
        """Restore volume from backup."""
        post_body = {'volume_id': volume_id}
        post_body = json.dumps({'restore': post_body})
        resp, body = self.post('backups/%s/restore' % (backup_id), post_body)
        body = json.loads(body)
        return resp, body['restore']

    def delete_backup(self, backup_id):
        """Delete a backup of volume."""
        resp, body = self.delete('backups/%s' % (str(backup_id)))
        return resp, body

    def get_backup(self, backup_id):
        """Returns the details of a single backup."""
        url = "backups/%s" % str(backup_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['backup']

    def wait_for_backup_status(self, backup_id, status):
        """Waits for a Backup to reach a given status."""
        resp, body = self.get_backup(backup_id)
        backup_status = body['status']
        start = int(time.time())

        while backup_status != status:
            time.sleep(self.build_interval)
            resp, body = self.get_backup(backup_id)
            backup_status = body['status']
            if backup_status == 'error':
                raise exceptions.VolumeBackupException(backup_id=backup_id)

            if int(time.time()) - start >= self.build_timeout:
                message = ('Volume backup %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (backup_id, status, self.build_timeout))
                raise exceptions.TimeoutException(message)
