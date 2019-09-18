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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc


class BackupsClient(rest_client.RestClient):
    """Volume V1 Backups client"""
    api_version = "v1"

    def create_backup(self, **kwargs):
        """Creates a backup of volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#create-backup
        """
        post_body = json.dumps({'backup': kwargs})
        resp, body = self.post('backups', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def restore_backup(self, backup_id, **kwargs):
        """Restore volume from backup.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#restore-backup
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

    def list_backups(self, detail=False):
        """Information for all the tenant's backups."""
        url = "backups"
        if detail:
            url += "/detail"
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
        # TODO(linanbj): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
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
