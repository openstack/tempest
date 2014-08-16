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
import urllib

from lxml import etree

from tempest.common import rest_client
from tempest.common import xml_utils as common
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SnapshotsClientXML(rest_client.RestClient):
    """Client class to send CRUD Volume API requests."""
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(SnapshotsClientXML, self).__init__(auth_provider)

        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.volume.build_interval
        self.build_timeout = CONF.volume.build_timeout

    def list_snapshots(self, params=None):
        """List all snapshot."""
        url = 'snapshots'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        snapshots = []
        for snap in body:
            snapshots.append(common.xml_to_json(snap))
        self.expected_success(200, resp.status)
        return resp, snapshots

    def list_snapshots_with_detail(self, params=None):
        """List all the details of snapshot."""
        url = 'snapshots/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        snapshots = []
        for snap in body:
            snapshots.append(common.xml_to_json(snap))
        self.expected_success(200, resp.status)
        return resp, snapshots

    def get_snapshot(self, snapshot_id):
        """Returns the details of a single snapshot."""
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.get(url)
        body = etree.fromstring(body)
        self.expected_success(200, resp.status)
        return resp, common.xml_to_json(body)

    def create_snapshot(self, volume_id, **kwargs):
        """Creates a new snapshot.
        volume_id(Required): id of the volume.
        force: Create a snapshot even if the volume attached (Default=False)
        display_name: Optional snapshot Name.
        display_description: User friendly snapshot description.
        """
        # NOTE(afazekas): it should use the volume namespace
        snapshot = common.Element("snapshot", xmlns=common.XMLNS_11,
                                  volume_id=volume_id)
        for key, value in kwargs.items():
            snapshot.add_attr(key, value)
        resp, body = self.post('snapshots',
                               str(common.Document(snapshot)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def update_snapshot(self, snapshot_id, **kwargs):
        """Updates a snapshot."""
        put_body = common.Element("snapshot", xmlns=common.XMLNS_11, **kwargs)

        resp, body = self.put('snapshots/%s' % snapshot_id,
                              str(common.Document(put_body)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

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
        self.expected_success(200, resp.status)

    def is_resource_deleted(self, id):
        try:
            self.get_snapshot(id)
        except exceptions.NotFound:
            return True
        return False

    def reset_snapshot_status(self, snapshot_id, status):
        """Reset the specified snapshot's status."""
        post_body = common.Element("os-reset_status", status=status)
        url = 'snapshots/%s/action' % str(snapshot_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(202, resp.status)
        return resp, body

    def update_snapshot_status(self, snapshot_id, status, progress):
        """Update the specified snapshot's status."""
        post_body = common.Element("os-update_snapshot_status",
                                   status=status,
                                   progress=progress
                                   )
        url = 'snapshots/%s/action' % str(snapshot_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(202, resp.status)
        return resp, body

    def _metadata_body(self, meta):
        post_body = common.Element('metadata')
        for k, v in meta.items():
            data = common.Element('meta', key=k)
            data.append(common.Text(v))
            post_body.append(data)
        return post_body

    def _parse_key_value(self, node):
        """Parse <foo key='key'>value</foo> data into {'key': 'value'}."""
        data = {}
        for node in node.getchildren():
            data[node.get('key')] = node.text
        return data

    def create_snapshot_metadata(self, snapshot_id, metadata):
        """Create metadata for the snapshot."""
        post_body = self._metadata_body(metadata)
        resp, body = self.post('snapshots/%s/metadata' % snapshot_id,
                               str(common.Document(post_body)))
        body = self._parse_key_value(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def get_snapshot_metadata(self, snapshot_id):
        """Get metadata of the snapshot."""
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.get(url)
        body = self._parse_key_value(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def update_snapshot_metadata(self, snapshot_id, metadata):
        """Update metadata for the snapshot."""
        put_body = self._metadata_body(metadata)
        url = "snapshots/%s/metadata" % str(snapshot_id)
        resp, body = self.put(url, str(common.Document(put_body)))
        body = self._parse_key_value(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def update_snapshot_metadata_item(self, snapshot_id, id, meta_item):
        """Update metadata item for the snapshot."""
        for k, v in meta_item.items():
            put_body = common.Element('meta', key=k)
            put_body.append(common.Text(v))
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.put(url, str(common.Document(put_body)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def delete_snapshot_metadata_item(self, snapshot_id, id):
        """Delete metadata item for the snapshot."""
        url = "snapshots/%s/metadata/%s" % (str(snapshot_id), str(id))
        resp, body = self.delete(url)
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def force_delete_snapshot(self, snapshot_id):
        """Force Delete Snapshot."""
        post_body = common.Element("os-force_delete")
        url = 'snapshots/%s/action' % str(snapshot_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(202, resp.status)
        return resp, body
