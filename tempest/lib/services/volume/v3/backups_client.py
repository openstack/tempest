# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume import base_client


class BackupsClient(base_client.BaseClient):
    """Volume V3 Backups client"""

    def create_backup(self, **kwargs):
        """Creates a backup of volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/index.html#create-a-backup
        """
        post_body = json.dumps({'backup': kwargs})
        resp, body = self.post('backups', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_backup(self, backup_id, **kwargs):
        """Updates the specified volume backup.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#update-a-backup
        """
        put_body = json.dumps({'backup': kwargs})
        resp, body = self.put('backups/%s' % backup_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def restore_backup(self, backup_id, **kwargs):
        """Restore volume from backup.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/index.html#restore-a-backup
        """
        post_body = json.dumps({'restore': kwargs})
        resp, body = self.post('backups/%s/restore' % (backup_id), post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_backup(self, backup_id):
        """Delete a backup of volume."""
        resp, body = self.delete('backups/%s' % backup_id)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_backup(self, backup_id):
        """Returns the details of a single backup."""
        url = "backups/%s" % backup_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_backups(self, detail=False, **params):
        """List all the tenant's backups.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/index.html#list-backups-for-project
        https://developer.openstack.org/api-ref/block-storage/v3/index.html#list-backups-with-detail
        """
        url = "backups"
        if detail:
            url += "/detail"
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def export_backup(self, backup_id):
        """Export backup metadata record."""
        url = "backups/%s/export_record" % backup_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def import_backup(self, **kwargs):
        """Import backup metadata record."""
        post_body = json.dumps({'backup-record': kwargs})
        resp, body = self.post("backups/import_record", post_body)
        body = json.loads(body)
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_backup_status(self, backup_id, status):
        """Reset the specified backup's status."""
        post_body = json.dumps({'os-reset_status': {"status": status}})
        resp, body = self.post('backups/%s/action' % backup_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_backup(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'backup'
