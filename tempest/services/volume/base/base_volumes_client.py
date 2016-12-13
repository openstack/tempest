# Copyright 2012 OpenStack Foundation
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
import six
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc


class BaseVolumesClient(rest_client.RestClient):
    """Base client class to send CRUD Volume API requests"""

    create_resp = 200

    def __init__(self, auth_provider, service, region,
                 default_volume_size=1, **kwargs):
        super(BaseVolumesClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.default_volume_size = default_volume_size

    def get_attachment_from_volume(self, volume):
        """Return the element 'attachment' from input volumes."""
        return volume['attachments'][0]

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.

        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_volumes(self, detail=False, params=None):
        """List all the volumes created.

        Params can be a string (must be urlencoded) or a dictionary.
        """
        url = 'volumes'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_pools(self, detail=False):
        # List all the volumes pools (hosts)
        url = 'scheduler-stats/get_pools'
        if detail:
            url += '?detail=True'

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume(self, **kwargs):
        """Creates a new Volume.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#createVolume
        """
        if 'size' not in kwargs:
            kwargs['size'] = self.default_volume_size
        post_body = json.dumps({'volume': kwargs})
        resp, body = self.post('volumes', post_body)
        body = json.loads(body)
        self.expected_success(self.create_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#updateVolume
        """
        put_body = json.dumps({'volume': kwargs})
        resp, body = self.put('volumes/%s' % volume_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume."""
        resp, body = self.delete("volumes/%s" % str(volume_id))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def upload_volume(self, volume_id, **kwargs):
        """Uploads a volume in Glance."""
        post_body = json.dumps({'os-volume_upload_image': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def attach_volume(self, volume_id, **kwargs):
        """Attaches a volume to a given instance on a given mountpoint.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#attachVolume
        """
        post_body = json.dumps({'os-attach': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def set_bootable_volume(self, volume_id, **kwargs):
        """set a bootable flag for a volume - true or false."""
        post_body = json.dumps({'os-set_bootable': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = json.dumps({'os-detach': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reserve_volume(self, volume_id):
        """Reserves a volume."""
        post_body = json.dumps({'os-reserve': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def unreserve_volume(self, volume_id):
        """Restore a reserved volume ."""
        post_body = json.dumps({'os-unreserve': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_volume(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'volume'

    def extend_volume(self, volume_id, **kwargs):
        """Extend a volume.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#extendVolume
        """
        post_body = json.dumps({'os-extend': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_volume_status(self, volume_id, **kwargs):
        """Reset the Specified Volume's Status.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#resetVolume
        """
        post_body = json.dumps({'os-reset_status': kwargs})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def volume_begin_detaching(self, volume_id):
        """Volume Begin Detaching."""
        # ref cinder/api/contrib/volume_actions.py#L158
        post_body = json.dumps({'os-begin_detaching': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def volume_roll_detaching(self, volume_id):
        """Volume Roll Detaching."""
        # cinder/api/contrib/volume_actions.py#L170
        post_body = json.dumps({'os-roll_detaching': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume_transfer(self, **kwargs):
        """Create a volume transfer.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#createVolumeTransfer
        """
        post_body = json.dumps({'transfer': kwargs})
        resp, body = self.post('os-volume-transfer', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_transfer(self, transfer_id):
        """Returns the details of a volume transfer."""
        url = "os-volume-transfer/%s" % str(transfer_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_volume_transfers(self, **params):
        """List all the volume transfers created.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#listVolumeTransfer
        """
        url = 'os-volume-transfer'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_transfer(self, transfer_id):
        """Delete a volume transfer."""
        resp, body = self.delete("os-volume-transfer/%s" % str(transfer_id))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def accept_volume_transfer(self, transfer_id, **kwargs):
        """Accept a volume transfer.

        Available params: see http://developer.openstack.org/
                                api-ref-blockstorage-v2.html#acceptVolumeTransfer
        """
        url = 'os-volume-transfer/%s/accept' % transfer_id
        post_body = json.dumps({'accept': kwargs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_readonly(self, volume_id, **kwargs):
        """Update the Specified Volume readonly."""
        post_body = json.dumps({'os-update_readonly_flag': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def force_delete_volume(self, volume_id):
        """Force Delete Volume."""
        post_body = json.dumps({'os-force_delete': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume_metadata(self, volume_id, metadata):
        """Create metadata for the volume."""
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.post(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_metadata(self, volume_id):
        """Get metadata of the volume."""
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_metadata(self, volume_id, metadata):
        """Update metadata for the volume."""
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_metadata_item(self, volume_id, id, meta_item):
        """Update metadata item for the volume."""
        put_body = json.dumps({'meta': meta_item})
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_metadata_item(self, volume_id, id):
        """Delete metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_image_metadata(self, volume_id, **kwargs):
        """Update image metadata for the volume.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html
                              #setVolumeimagemetadata
        """
        post_body = json.dumps({'os-set_image_metadata': {'metadata': kwargs}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_image_metadata(self, volume_id, key_name):
        """Delete image metadata item for the volume."""
        post_body = json.dumps({'os-unset_image_metadata': {'key': key_name}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def retype_volume(self, volume_id, **kwargs):
        """Updates volume with new volume type."""
        post_body = json.dumps({'os-retype': kwargs})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
