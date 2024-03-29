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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import backups as schema
from tempest.lib.api_schema.response.volume.v3_64 import backups as schemav364
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume import base_client


class BackupsClient(base_client.BaseClient):
    """Volume V3 Backups client"""

    schema_versions_info = [
        {'min': None, 'max': '3.63', 'schema': schema},
        {'min': '3.64', 'max': None, 'schema': schemav364}
        ]

    def create_backup(self, **kwargs):
        """Creates a backup of volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-a-backup
        """
        post_body = json.dumps({'backup': kwargs})
        resp, body = self.post('backups', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_backup(self, backup_id, **kwargs):
        """Updates the specified volume backup.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#update-a-backup
        """
        put_body = json.dumps({'backup': kwargs})
        resp, body = self.put('backups/%s' % backup_id, put_body)
        body = json.loads(body)
        self.validate_response(schema.update_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def restore_backup(self, backup_id, **kwargs):
        """Restore volume from backup.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#restore-a-backup
        """
        post_body = json.dumps({'restore': kwargs})
        resp, body = self.post('backups/%s/restore' % (backup_id), post_body)
        body = json.loads(body)
        self.validate_response(schema.restore_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_backup(self, backup_id):
        """Delete a backup of volume."""
        resp, body = self.delete('backups/%s' % backup_id)
        self.validate_response(schema.delete_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_backup(self, backup_id):
        """Returns the details of a single backup."""
        url = "backups/%s" % backup_id
        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.show_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_backups(self, detail=False, **params):
        """List all the tenant's backups.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-backups-for-project
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-backups-with-detail
        """
        url = "backups"
        schema = self.get_schema(self.schema_versions_info)
        list_backups_schema = schema.list_backups_no_detail
        if detail:
            url += "/detail"
            list_backups_schema = schema.list_backups_with_detail
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(list_backups_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def export_backup(self, backup_id):
        """Export backup metadata record."""
        url = "backups/%s/export_record" % backup_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.export_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def import_backup(self, **kwargs):
        """Import backup metadata record.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#import-a-backup
        """
        post_body = json.dumps({'backup-record': kwargs})
        resp, body = self.post("backups/import_record", post_body)
        body = json.loads(body)
        self.validate_response(schema.import_backup, resp, body)
        return rest_client.ResponseBody(resp, body)

    def reset_backup_status(self, backup_id, status):
        """Reset the specified backup's status."""
        post_body = json.dumps({'os-reset_status': {"status": status}})
        resp, body = self.post('backups/%s/action' % backup_id, post_body)
        self.validate_response(schema.reset_backup_status, resp, body)
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
