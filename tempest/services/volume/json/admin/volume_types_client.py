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
import urllib

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class VolumeTypesClientJSON(rest_client.RestClient):
    """
    Client class to send CRUD Volume Types API requests to a Cinder endpoint
    """

    def __init__(self, auth_provider):
        super(VolumeTypesClientJSON, self).__init__(auth_provider)

        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.volume.build_interval
        self.build_timeout = CONF.volume.build_timeout

    def list_volume_types(self, params=None):
        """List all the volume_types created."""
        url = 'types'
        if params is not None:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volume_types']

    def get_volume_type(self, volume_id):
        """Returns the details of a single volume_type."""
        url = "types/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['volume_type']

    def create_volume_type(self, name, **kwargs):
        """
        Creates a new Volume_type.
        name(Required): Name of volume_type.
        Following optional keyword arguments are accepted:
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        post_body = {
            'name': name,
            'extra_specs': kwargs.get('extra_specs'),
        }

        post_body = json.dumps({'volume_type': post_body})
        resp, body = self.post('types', post_body)
        body = json.loads(body)
        return resp, body['volume_type']

    def delete_volume_type(self, volume_id):
        """Deletes the Specified Volume_type."""
        return self.delete("types/%s" % str(volume_id))

    def list_volume_types_extra_specs(self, vol_type_id, params=None):
        """List all the volume_types extra specs created."""
        url = 'types/%s/extra_specs' % str(vol_type_id)
        if params is not None:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['extra_specs']

    def get_volume_type_extra_specs(self, vol_type_id, extra_spec_name):
        """Returns the details of a single volume_type extra spec."""
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def create_volume_type_extra_specs(self, vol_type_id, extra_spec):
        """
        Creates a new Volume_type extra spec.
        vol_type_id: Id of volume_type.
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        url = "types/%s/extra_specs" % str(vol_type_id)
        post_body = json.dumps({'extra_specs': extra_spec})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        return resp, body['extra_specs']

    def delete_volume_type_extra_specs(self, vol_id, extra_spec_name):
        """Deletes the Specified Volume_type extra spec."""
        return self.delete("types/%s/extra_specs/%s" % ((str(vol_id)),
                                                        str(extra_spec_name)))

    def update_volume_type_extra_specs(self, vol_type_id, extra_spec_name,
                                       extra_spec):
        """
        Update a volume_type extra spec.
        vol_type_id: Id of volume_type.
        extra_spec_name: Name of the extra spec to be updated.
        extra_spec: A dictionary of with key as extra_spec_name and the
                     updated value.
        """
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        put_body = json.dumps(extra_spec)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        return resp, body
