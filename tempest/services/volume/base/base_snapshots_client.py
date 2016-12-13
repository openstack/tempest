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


class BaseSnapshotsClient(rest_client.RestClient):
    """Base Client class to send CRUD Volume API requests."""

    create_resp = 200

    def list_snapshots(self, detail=False, **params):
        """List all the snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#listSnapshots
        """
        url = 'snapshots'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_snapshot(self, snapshot_id):
        """Returns the details of a single snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#showSnapshot
        """
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_snapshot(self, **kwargs):
        """Creates a new snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#createSnapshot
        """
        post_body = json.dumps({'snapshot': kwargs})
        resp, body = self.post('snapshots', post_body)
        body = json.loads(body)
        self.expected_success(self.create_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_snapshot(self, snapshot_id, **kwargs):
        """Updates a snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#updateSnapshot
        """
        put_body = json.dumps({'snapshot': kwargs})
        resp, body = self.put('snapshots/%s' % snapshot_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_snapshot(self, snapshot_id):
        """Delete Snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#deleteSnapshot
        """
        resp, body = self.delete("snapshots/%s" % str(snapshot_id))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_snapshot(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'volume-snapshot'

    def reset_snapshot_status(self, snapshot_id, status):
        """Reset the specified snapshot's status."""
        post_body = json.dumps({'os-reset_status': {"status": status}})
        resp, body = self.post('snapshots/%s/action' % snapshot_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_snapshot_status(self, snapshot_id, **kwargs):
        """Update the specified snapshot's status."""
        # TODO(gmann): api-site doesn't contain doc ref
        # for this API. After fixing the api-site, we need to
        # add the link here.
        # Bug https://bugs.launchpad.net/openstack-api-site/+bug/1532645

        post_body = json.dumps({'os-update_snapshot_status': kwargs})
        url = 'snapshots/%s/action' % str(snapshot_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_snapshot_metadata(self, snapshot_id, metadata):
        """Create metadata for the snapshot."""
        put_body = json.dumps({'metadata': metadata})
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.post(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_snapshot_metadata(self, snapshot_id):
        """Get metadata of the snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#
                              showSnapshotMetadata
        """
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_snapshot_metadata(self, snapshot_id, **kwargs):
        """Update metadata for the snapshot.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#
                              updateSnapshotMetadata
        """
        put_body = json.dumps(kwargs)
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_snapshot_metadata_item(self, snapshot_id, id, **kwargs):
        """Update metadata item for the snapshot."""
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1529064
        put_body = json.dumps(kwargs)
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_snapshot_metadata_item(self, snapshot_id, id):
        """Delete metadata item for the snapshot."""
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def force_delete_snapshot(self, snapshot_id):
        """Force Delete Snapshot."""
        post_body = json.dumps({'os-force_delete': {}})
        resp, body = self.post('snapshots/%s/action' % snapshot_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)
