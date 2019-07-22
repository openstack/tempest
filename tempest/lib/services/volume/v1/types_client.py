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
from six.moves.urllib import parse as urllib

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
        """List all the volume_types created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#list-all-volume-types-for-v2
        """
        url = 'types'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_type(self, volume_type_id):
        """Returns the details of a single volume_type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#show-volume-type-details-for-v2
        """
        url = "types/%s" % volume_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume_type(self, **kwargs):
        """Create volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#create-volume-type-for-v2
        """
        post_body = json.dumps({'volume_type': kwargs})
        resp, body = self.post('types', post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_type(self, volume_type_id):
        """Deletes the Specified Volume_type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#delete-volume-type
        """
        resp, body = self.delete("types/%s" % volume_type_id)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_volume_types_extra_specs(self, volume_type_id, **params):
        """List all the volume_types extra specs created.

        TODO: Current api-site doesn't contain this API description.
        After fixing the api-site, we need to fix here also for putting
        the link to api-site.
        """
        url = 'types/%s/extra_specs' % volume_type_id
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_type_extra_specs(self, volume_type_id, extra_specs_name):
        """Returns the details of a single volume_type extra spec."""
        url = "types/%s/extra_specs/%s" % (volume_type_id, extra_specs_name)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume_type_extra_specs(self, volume_type_id, extra_specs):
        """Creates a new Volume_type extra spec.

        volume_type_id: Id of volume_type.
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        url = "types/%s/extra_specs" % volume_type_id
        post_body = json.dumps({'extra_specs': extra_specs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_type_extra_specs(self, volume_type_id, extra_spec_name):
        """Deletes the Specified Volume_type extra spec."""
        resp, body = self.delete("types/%s/extra_specs/%s" % (
            volume_type_id, extra_spec_name))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_type(self, volume_type_id, **kwargs):
        """Updates volume type name, description, and/or is_public.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#update-volume-type
        """
        put_body = json.dumps({'volume_type': kwargs})
        resp, body = self.put('types/%s' % volume_type_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_type_extra_specs(self, volume_type_id, extra_spec_name,
                                       extra_specs):
        """Update a volume_type extra spec.

        :param volume_type_id: Id of volume_type.
        :param extra_spec_name: Name of the extra spec to be updated.
        :param extra_specs: A dictionary of with key as extra_spec_name and the
                            updated value.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#update-extra-specs-for-a-volume-type
        """
        url = "types/%s/extra_specs/%s" % (volume_type_id, extra_spec_name)
        put_body = json.dumps(extra_specs)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
