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

from tempest_lib import exceptions as lib_exc

from tempest.common import service_client


class BaseVolumeTypesClientJSON(service_client.ServiceClient):
    """
    Client class to send CRUD Volume Types API requests to a Cinder endpoint
    """

    def is_resource_deleted(self, resource):
        # to use this method self.resource must be defined to respective value
        # Resource is a dictionary containing resource id and type
        # Resource : {"id" : resource_id
        #             "type": resource_type}
        try:
            if resource['type'] == "volume-type":
                self.show_volume_type(resource['id'])
            elif resource['type'] == "encryption-type":
                body = self.show_encryption_type(resource['id'])
                if not body:
                    return True
            else:
                msg = (" resource value is either not defined or incorrect.")
                raise lib_exc.UnprocessableEntity(msg)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'volume-type/encryption-type'

    def list_volume_types(self, params=None):
        """List all the volume_types created."""
        url = 'types'
        if params is not None:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyList(resp, body['volume_types'])

    def show_volume_type(self, volume_id):
        """Returns the details of a single volume_type."""
        url = "types/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['volume_type'])

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
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['volume_type'])

    def delete_volume_type(self, volume_id):
        """Deletes the Specified Volume_type."""
        resp, body = self.delete("types/%s" % str(volume_id))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_volume_types_extra_specs(self, vol_type_id, params=None):
        """List all the volume_types extra specs created."""
        url = 'types/%s/extra_specs' % str(vol_type_id)
        if params is not None:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['extra_specs'])

    def show_volume_type_extra_specs(self, vol_type_id, extra_spec_name):
        """Returns the details of a single volume_type extra spec."""
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)

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
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['extra_specs'])

    def delete_volume_type_extra_specs(self, vol_id, extra_spec_name):
        """Deletes the Specified Volume_type extra spec."""
        resp, body = self.delete("types/%s/extra_specs/%s" % (
            (str(vol_id)), str(extra_spec_name)))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

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
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)

    def show_encryption_type(self, vol_type_id):
        """
        Get the volume encryption type for the specified volume type.
        vol_type_id: Id of volume_type.
        """
        url = "/types/%s/encryption" % str(vol_type_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)

    def create_encryption_type(self, vol_type_id, **kwargs):
        """
        Create a new encryption type for the specified volume type.

        vol_type_id: Id of volume_type.
        provider: Class providing encryption support.
        cipher: Encryption algorithm/mode to use.
        key_size: Size of the encryption key, in bits.
        control_location: Notional service where encryption is performed.
        """
        url = "/types/%s/encryption" % str(vol_type_id)
        post_body = {}
        post_body.update(kwargs)
        post_body = json.dumps({'encryption': post_body})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body['encryption'])

    def delete_encryption_type(self, vol_type_id):
        """Delete the encryption type for the specified volume-type."""
        resp, body = self.delete(
            "/types/%s/encryption/provider" % str(vol_type_id))
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)


class VolumeTypesClientJSON(BaseVolumeTypesClientJSON):
    """Volume V1 Volume Types client"""
