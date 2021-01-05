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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import volume_types as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc


class TypesClient(rest_client.RestClient):
    """Client class to send CRUD Volume Types API requests"""

    def is_resource_deleted(self, id):
        try:
            self.show_volume_type(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'volume-type'

    def list_volume_types(self, **params):
        """List all the volume types created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-all-volume-types
        """
        url = 'types'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_volume_types, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume_type(self, volume_type_id):
        """Returns the details of a single volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#show-volume-type-detail
        """
        url = "types/%s" % volume_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_volume_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_default_volume_type(self):
        """Returns the details of a single volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#show-default-volume-type
        """
        url = "types/default"
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_volume_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_volume_type(self, **kwargs):
        """Create volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-a-volume-type
        """
        post_body = json.dumps({'volume_type': kwargs})
        resp, body = self.post('types', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_volume_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_type(self, volume_type_id):
        """Deletes the specified volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#delete-a-volume-type
        """
        resp, body = self.delete("types/%s" % volume_type_id)
        self.validate_response(schema.delete_volume_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_volume_types_extra_specs(self, volume_type_id, **params):
        """List all the volume type extra specs created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#show-all-extra-specifications-for-volume-type
        """
        url = 'types/%s/extra_specs' % volume_type_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(
            schema.list_volume_types_extra_specs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume_type_extra_specs(self, volume_type_id, extra_specs_name):
        """Returns the details of a single volume type extra spec."""
        url = "types/%s/extra_specs/%s" % (volume_type_id, extra_specs_name)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(
            schema.show_volume_types_extra_specs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_volume_type_extra_specs(self, volume_type_id, extra_specs):
        """Creates new volume type extra specs.

        :param volume_type_id: Id of volume type.
        :param extra_specs: A dictionary of values to be used as extra_specs.
        """
        url = "types/%s/extra_specs" % volume_type_id
        post_body = json.dumps({'extra_specs': extra_specs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(
            schema.create_volume_types_extra_specs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_type_extra_specs(self, volume_type_id, extra_spec_name):
        """Deletes the specified volume type extra spec."""
        resp, body = self.delete("types/%s/extra_specs/%s" % (
            volume_type_id, extra_spec_name))
        self.validate_response(
            schema.delete_volume_types_extra_specs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_volume_type(self, volume_type_id, **kwargs):
        """Updates volume type name, description, and/or is_public.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-a-volume-type
        """
        put_body = json.dumps({'volume_type': kwargs})
        resp, body = self.put('types/%s' % volume_type_id, put_body)
        body = json.loads(body)
        self.validate_response(schema.update_volume_types, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_volume_type_extra_specs(self, volume_type_id, extra_spec_name,
                                       extra_specs):
        """Update a volume_type extra spec.

        :param volume_type_id: Id of volume type.
        :param extra_spec_name: Name of the extra spec to be updated.
        :param extra_specs: A dictionary of with key as extra_spec_name and the
                            updated value.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-extra-specification-for-volume-type
        """
        url = "types/%s/extra_specs/%s" % (volume_type_id, extra_spec_name)
        put_body = json.dumps(extra_specs)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.validate_response(
            schema.update_volume_type_extra_specs, resp, body)
        return rest_client.ResponseBody(resp, body)

    def add_type_access(self, volume_type_id, **kwargs):
        """Adds volume type access for the given project.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#add-private-volume-type-access-to-project
        """
        post_body = json.dumps({'addProjectAccess': kwargs})
        url = 'types/%s/action' % volume_type_id
        resp, body = self.post(url, post_body)
        self.validate_response(schema.add_type_access, resp, body)
        return rest_client.ResponseBody(resp, body)

    def remove_type_access(self, volume_type_id, **kwargs):
        """Removes volume type access for the given project.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#remove-private-volume-type-access-from-project
        """
        post_body = json.dumps({'removeProjectAccess': kwargs})
        url = 'types/%s/action' % volume_type_id
        resp, body = self.post(url, post_body)
        self.validate_response(schema.remove_type_access, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_type_access(self, volume_type_id):
        """Print access information about the given volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-private-volume-type-access-detail
        """
        url = 'types/%s/os-volume-type-access' % volume_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_type_access, resp, body)
        return rest_client.ResponseBody(resp, body)
