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
import urllib

from tempest.common import rest_client
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SnapshotsClientJSON(rest_client.RestClient):
    """Client class to send CRUD Volume API requests."""

    def __init__(self, auth_provider):
        super(SnapshotsClientJSON, self).__init__(auth_provider)

        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.volume.build_interval
        self.build_timeout = CONF.volume.build_timeout

    def list_snapshots(self, params=None):
        """List all the snapshot."""
        url = 'snapshots'
        if params:
                url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['snapshots']

    def list_snapshots_with_detail(self, params=None):
        """List the details of all snapshots."""
        url = 'snapshots/detail'
        if params:
                url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['snapshots']

    def get_snapshot(self, snapshot_id):
        """Returns the details of a single snapshot."""
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['snapshot']

    def create_snapshot(self, volume_id, **kwargs):
        """
        Creates a new snapshot.
        volume_id(Required): id of the volume.
        force: Create a snapshot even if the volume attached (Default=False)
        display_name: Optional snapshot Name.
        display_description: User friendly snapshot description.
        """
        post_body = {'volume_id': volume_id}
        post_body.update(kwargs)
        post_body = json.dumps({'snapshot': post_body})
        resp, body = self.post('snapshots', post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['snapshot']

    def update_snapshot(self, snapshot_id, **kwargs):
        """Updates a snapshot."""
        put_body = json.dumps({'snapshot': kwargs})
        resp, body = self.put('snapshots/%s' % snapshot_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['snapshot']

    # NOTE(afazekas): just for the wait function
    def _get_snapshot_status(self, snapshot_id):
        resp, body = self.get_snapshot(snapshot_id)
        status = body['status']
        # NOTE(afazekas): snapshot can reach an "error"
        # state in a "normal" lifecycle
        if (status == 'error'):
            raise exceptions.SnapshotBuildErrorException(
                snapshot_id=snapshot_id)

        return status

    # NOTE(afazkas): Wait reinvented again. It is not in the correct layer
    def wait_for_snapshot_status(self, snapshot_id, status):
        """Waits for a Snapshot to reach a given status."""
        start_time = time.time()
        old_value = value = self._get_snapshot_status(snapshot_id)
        while True:
            dtime = time.time() - start_time
            time.sleep(self.build_interval)
            if value != old_value:
                LOG.info('Value transition from "%s" to "%s"'
                         'in %d second(s).', old_value,
                         value, dtime)
            if (value == status):
                return value

            if dtime > self.build_timeout:
                message = ('Time Limit Exceeded! (%ds)'
                           'while waiting for %s, '
                           'but we got %s.' %
                           (self.build_timeout, status, value))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)
            old_value = value
            value = self._get_snapshot_status(snapshot_id)

    def delete_snapshot(self, snapshot_id):
        """Delete Snapshot."""
        resp, body = self.delete("snapshots/%s" % str(snapshot_id))
        self.expected_success(202, resp.status)

    def is_resource_deleted(self, id):
        try:
            self.get_snapshot(id)
        except exceptions.NotFound:
            return True
        return False

    def reset_snapshot_status(self, snapshot_id, status):
        """Reset the specified snapshot's status."""
        post_body = json.dumps({'os-reset_status': {"status": status}})
        resp, body = self.post('snapshots/%s/action' % snapshot_id, post_body)
        self.expected_success(202, resp.status)
        return resp, body

    def update_snapshot_status(self, snapshot_id, status, progress):
        """Update the specified snapshot's status."""
        post_body = {
            'status': status,
            'progress': progress
        }
        post_body = json.dumps({'os-update_snapshot_status': post_body})
        url = 'snapshots/%s/action' % str(snapshot_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return resp, body

    def create_snapshot_metadata(self, snapshot_id, metadata):
        """Create metadata for the snapshot."""
        put_body = json.dumps({'metadata': metadata})
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.post(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['metadata']

    def get_snapshot_metadata(self, snapshot_id):
        """Get metadata of the snapshot."""
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['metadata']

    def update_snapshot_metadata(self, snapshot_id, metadata):
        """Update metadata for the snapshot."""
        put_body = json.dumps({'metadata': metadata})
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['metadata']

    def update_snapshot_metadata_item(self, snapshot_id, id, meta_item):
        """Update metadata item for the snapshot."""
        put_body = json.dumps({'meta': meta_item})
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body['meta']

    def delete_snapshot_metadata_item(self, snapshot_id, id):
        """Delete metadata item for the snapshot."""
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)

    def force_delete_snapshot(self, snapshot_id):
        """Force Delete Snapshot."""
        post_body = json.dumps({'os-force_delete': {}})
        resp, body = self.post('snapshots/%s/action' % snapshot_id, post_body)
        self.expected_success(202, resp.status)
        return resp, body
