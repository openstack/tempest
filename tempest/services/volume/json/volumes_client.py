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

import json
import time
import urllib

from tempest_lib import exceptions as lib_exc

from tempest.common import service_client
from tempest import exceptions


class BaseVolumesClientJSON(service_client.ServiceClient):
    """
    Base client class to send CRUD Volume API requests to a Cinder endpoint
    """

    create_resp = 200

    def __init__(self, auth_provider, service, region,
                 default_volume_size=1, **kwargs):
        super(BaseVolumesClientJSON, self).__init__(
            auth_provider, service, region, **kwargs)
        self.default_volume_size = default_volume_size

    def get_attachment_from_volume(self, volume):
        """Return the element 'attachment' from input volumes."""
        return volume['attachments'][0]

    def list_volumes(self, detail=False, params=None):
        """List all the volumes created."""
        url = 'volumes'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyList(resp, body['volumes'])

    def show_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['volume'])

    def create_volume(self, size=None, **kwargs):
        """
        Creates a new Volume.
        size: Size of volume in GB.
        Following optional keyword arguments are accepted:
        display_name: Optional Volume Name(only for V1).
        name: Optional Volume Name(only for V2).
        metadata: A dictionary of values to be used as metadata.
        volume_type: Optional Name of volume_type for the volume
        snapshot_id: When specified the volume is created from this snapshot
        imageRef: When specified the volume is created from this image
        """
        if size is None:
            size = self.default_volume_size
        post_body = {'size': size}
        post_body.update(kwargs)
        post_body = json.dumps({'volume': post_body})
        resp, body = self.post('volumes', post_body)
        body = json.loads(body)
        self.expected_success(self.create_resp, resp.status)
        return service_client.ResponseBody(resp, body['volume'])

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume."""
        put_body = json.dumps({'volume': kwargs})
        resp, body = self.put('volumes/%s' % volume_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['volume'])

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume."""
        resp, body = self.delete("volumes/%s" % str(volume_id))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def upload_volume(self, volume_id, image_name, disk_format):
        """Uploads a volume in Glance."""
        post_body = {
            'image_name': image_name,
            'disk_format': disk_format
        }
        post_body = json.dumps({'os-volume_upload_image': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp,
                                           body['os-volume_upload_image'])

    def attach_volume(self, volume_id, instance_uuid, mountpoint):
        """Attaches a volume to a given instance on a given mountpoint."""
        post_body = {
            'instance_uuid': instance_uuid,
            'mountpoint': mountpoint,
        }
        post_body = json.dumps({'os-attach': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = {}
        post_body = json.dumps({'os-detach': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def reserve_volume(self, volume_id):
        """Reserves a volume."""
        post_body = {}
        post_body = json.dumps({'os-reserve': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def unreserve_volume(self, volume_id):
        """Restore a reserved volume ."""
        post_body = {}
        post_body = json.dumps({'os-unreserve': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status."""
        body = self.show_volume(volume_id)
        volume_status = body['status']
        start = int(time.time())

        while volume_status != status:
            time.sleep(self.build_interval)
            body = self.show_volume(volume_id)
            volume_status = body['status']
            if volume_status == 'error':
                raise exceptions.VolumeBuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = ('Volume %s failed to reach %s status (current: %s) '
                           'within the required time '
                           '(%s s).' % (volume_id,
                                        status,
                                        volume_status,
                                        self.build_timeout))
                raise exceptions.TimeoutException(message)

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

    def extend_volume(self, volume_id, extend_size):
        """Extend a volume."""
        post_body = {
            'new_size': extend_size
        }
        post_body = json.dumps({'os-extend': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def reset_volume_status(self, volume_id, status):
        """Reset the Specified Volume's Status."""
        post_body = json.dumps({'os-reset_status': {"status": status}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def volume_begin_detaching(self, volume_id):
        """Volume Begin Detaching."""
        # ref cinder/api/contrib/volume_actions.py#L158
        post_body = json.dumps({'os-begin_detaching': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def volume_roll_detaching(self, volume_id):
        """Volume Roll Detaching."""
        # cinder/api/contrib/volume_actions.py#L170
        post_body = json.dumps({'os-roll_detaching': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def create_volume_transfer(self, vol_id, display_name=None):
        """Create a volume transfer."""
        post_body = {
            'volume_id': vol_id
        }
        if display_name:
            post_body['name'] = display_name
        post_body = json.dumps({'transfer': post_body})
        resp, body = self.post('os-volume-transfer', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body['transfer'])

    def show_volume_transfer(self, transfer_id):
        """Returns the details of a volume transfer."""
        url = "os-volume-transfer/%s" % str(transfer_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['transfer'])

    def list_volume_transfers(self, params=None):
        """List all the volume transfers created."""
        url = 'os-volume-transfer'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyList(resp, body['transfers'])

    def delete_volume_transfer(self, transfer_id):
        """Delete a volume transfer."""
        resp, body = self.delete("os-volume-transfer/%s" % str(transfer_id))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def accept_volume_transfer(self, transfer_id, transfer_auth_key):
        """Accept a volume transfer."""
        post_body = {
            'auth_key': transfer_auth_key,
        }
        url = 'os-volume-transfer/%s/accept' % transfer_id
        post_body = json.dumps({'accept': post_body})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body['transfer'])

    def update_volume_readonly(self, volume_id, readonly):
        """Update the Specified Volume readonly."""
        post_body = {
            'readonly': readonly
        }
        post_body = json.dumps({'os-update_readonly_flag': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def force_delete_volume(self, volume_id):
        """Force Delete Volume."""
        post_body = json.dumps({'os-force_delete': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def create_volume_metadata(self, volume_id, metadata):
        """Create metadata for the volume."""
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.post(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['metadata'])

    def show_volume_metadata(self, volume_id):
        """Get metadata of the volume."""
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['metadata'])

    def update_volume_metadata(self, volume_id, metadata):
        """Update metadata for the volume."""
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['metadata'])

    def update_volume_metadata_item(self, volume_id, id, meta_item):
        """Update metadata item for the volume."""
        put_body = json.dumps({'meta': meta_item})
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['meta'])

    def delete_volume_metadata_item(self, volume_id, id):
        """Delete metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)

    def retype_volume(self, volume_id, volume_type, **kwargs):
        """Updates volume with new volume type."""
        post_body = {'new_type': volume_type}
        post_body.update(kwargs)
        post_body = json.dumps({'os-retype': post_body})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)


class VolumesClientJSON(BaseVolumesClientJSON):
    """
    Client class to send CRUD Volume V1 API requests to a Cinder endpoint
    """
