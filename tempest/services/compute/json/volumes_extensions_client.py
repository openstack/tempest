# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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


class VolumesExtensionsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumesExtensionsClientJSON, self).__init__(config, username,
                                                          password, auth_url,
                                                          tenant_name)
        self.service = self.config.compute.catalog_type
        self.build_interval = self.config.volume.build_interval
        self.build_timeout = self.config.volume.build_timeout

    def list_volumes(self, params=None):
        """List all the volumes created."""
        url = 'os-volumes'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes."""
        url = 'os-volumes/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def get_volume(self, volume_id, wait=None):
        """Returns the details of a single volume."""
        url = "os-volumes/%s" % str(volume_id)
        resp, body = self.get(url, wait=wait)
        body = json.loads(body)
        return resp, body['volume']

    def create_volume(self, size, **kwargs):
        """
        Creates a new Volume.
        size(Required): Size of volume in GB.
        Following optional keyword arguments are accepted:
        display_name: Optional Volume Name.
        metadata: A dictionary of values to be used as metadata.
        """
        post_body = {
            'size': size,
            'display_name': kwargs.get('display_name'),
            'metadata': kwargs.get('metadata'),
        }

        post_body = json.dumps({'volume': post_body})
        resp, body = self.post('os-volumes', post_body, self.headers)
        body = json.loads(body)
        return resp, body['volume']

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume."""
        return self.delete("os-volumes/%s" % str(volume_id))

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status."""
        resp, body = self.get_volume(volume_id)
        volume_name = body['displayName']
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
            self.get_volume(id, wait=True)
        except exceptions.NotFound:
            return True
        return False
