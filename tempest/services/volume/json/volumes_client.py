# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.common.rest_client import RestClient
from tempest import exceptions


class VolumesClientJSON(RestClient):
    """
    Client class to send CRUD Volume API requests to a Cinder endpoint
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumesClientJSON, self).__init__(config, username, password,
                                                auth_url, tenant_name)

        self.service = self.config.volume.catalog_type
        self.build_interval = self.config.volume.build_interval
        self.build_timeout = self.config.volume.build_timeout

    def get_attachment_from_volume(self, volume):
        """Return the element 'attachment' from input volumes."""
        return volume['attachments'][0]

    def list_volumes(self, params=None):
        """List all the volumes created."""
        url = 'volumes'
        if params:
                url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def list_volumes_with_detail(self, params=None):
        """List the details of all volumes."""
        url = 'volumes/detail'
        if params:
                url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def get_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volume']

    def create_volume(self, size, **kwargs):
        """
        Creates a new Volume.
        size(Required): Size of volume in GB.
        Following optional keyword arguments are accepted:
        display_name: Optional Volume Name.
        metadata: A dictionary of values to be used as metadata.
        volume_type: Optional Name of volume_type for the volume
        snapshot_id: When specified the volume is created from this snapshot
        imageRef: When specified the volume is created from this image
        """
        post_body = {'size': size}
        post_body.update(kwargs)
        post_body = json.dumps({'volume': post_body})
        resp, body = self.post('volumes', post_body, self.headers)
        body = json.loads(body)
        return resp, body['volume']

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume."""
        put_body = json.dumps({'volume': kwargs})
        resp, body = self.put('volumes/%s' % volume_id, put_body,
                              self.headers)
        body = json.loads(body)
        return resp, body['volume']

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume."""
        return self.delete("volumes/%s" % str(volume_id))

    def upload_volume(self, volume_id, image_name, disk_format):
        """Uploads a volume in Glance."""
        post_body = {
            'image_name': image_name,
            'disk_format': disk_format
        }
        post_body = json.dumps({'os-volume_upload_image': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body, self.headers)
        body = json.loads(body)
        return resp, body['os-volume_upload_image']

    def attach_volume(self, volume_id, instance_uuid, mountpoint):
        """Attaches a volume to a given instance on a given mountpoint."""
        post_body = {
            'instance_uuid': instance_uuid,
            'mountpoint': mountpoint,
        }
        post_body = json.dumps({'os-attach': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body, self.headers)
        return resp, body

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = {}
        post_body = json.dumps({'os-detach': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body, self.headers)
        return resp, body

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status."""
        resp, body = self.get_volume(volume_id)
        volume_name = body['display_name']
        volume_status = body['status']
        start = int(time.time())

        while volume_status != status:
            time.sleep(self.build_interval)
            resp, body = self.get_volume(volume_id)
            volume_status = body['status']
            if volume_status == 'error':
                raise exceptions.VolumeBuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = ('Volume %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (volume_name, status, self.build_timeout))
                raise exceptions.TimeoutException(message)

    def is_resource_deleted(self, id):
        try:
            self.get_volume(id)
        except exceptions.NotFound:
            return True
        return False

    def extend_volume(self, volume_id, extend_size):
        """Extend a volume."""
        post_body = {
            'new_size': extend_size
        }
        post_body = json.dumps({'os-extend': post_body})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body, self.headers)
        return resp, body
