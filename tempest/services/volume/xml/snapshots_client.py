# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11

LOG = logging.getLogger(__name__)


class SnapshotsClientXML(RestClientXML):
    """Client class to send CRUD Volume API requests."""

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(SnapshotsClientXML, self).__init__(config, username, password,
                                                 auth_url, tenant_name)

        self.service = self.config.volume.catalog_type
        self.build_interval = self.config.volume.build_interval
        self.build_timeout = self.config.volume.build_timeout

    def list_snapshots(self, params=None):
        """List all snapshot."""
        url = 'snapshots'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        snapshots = []
        for snap in body:
            snapshots.append(xml_to_json(snap))
        return resp, snapshots

    def list_snapshots_with_detail(self, params=None):
        """List all the details of snapshot."""
        url = 'snapshots/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        snapshots = []
        for snap in body:
            snapshots.append(xml_to_json(snap))
        return resp, snapshots

    def get_snapshot(self, snapshot_id):
        """Returns the details of a single snapshot."""
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        return resp, xml_to_json(body)

    def create_snapshot(self, volume_id, **kwargs):
        """Creates a new snapshot.
        volume_id(Required): id of the volume.
        force: Create a snapshot even if the volume attached (Default=False)
        display_name: Optional snapshot Name.
        display_description: User friendly snapshot description.
        """
        # NOTE(afazekas): it should use the volume namespace
        snapshot = Element("snapshot", xmlns=XMLNS_11, volume_id=volume_id)
        for key, value in kwargs.items():
            snapshot.add_attr(key, value)
        resp, body = self.post('snapshots', str(Document(snapshot)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
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
        return self.delete("snapshots/%s" % str(snapshot_id))

    def is_resource_deleted(self, id):
        try:
            self.get_snapshot(id)
        except exceptions.NotFound:
            return True
        return False
