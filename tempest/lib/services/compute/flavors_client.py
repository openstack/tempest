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

from tempest.lib.api_schema.response.compute.v2_1 import flavors as schema
from tempest.lib.api_schema.response.compute.v2_1 import flavors_access \
    as schema_access
from tempest.lib.api_schema.response.compute.v2_1 import flavors_extra_specs \
    as schema_extra_specs
from tempest.lib.api_schema.response.compute.v2_55 import flavors \
    as schemav255
from tempest.lib.api_schema.response.compute.v2_61 import flavors \
    as schemav261
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class FlavorsClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.54', 'schema': schema},
        {'min': '2.55', 'max': '2.60', 'schema': schemav255},
        {'min': '2.61', 'max': None, 'schema': schemav261}]

    def list_flavors(self, detail=False, **params):
        """Lists flavors.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-flavors
        https://docs.openstack.org/api-ref/compute/#list-flavors-with-details
        """
        url = 'flavors'
        schema = self.get_schema(self.schema_versions_info)
        if detail:
            url += '/detail'
            _schema = schema.list_flavors_details
        else:
            _schema = schema.list_flavors
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_flavor(self, flavor_id):
        """Shows details for a flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#show-flavor-details
        """
        resp, body = self.get("flavors/%s" % flavor_id)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.create_update_get_flavor_details,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_flavor(self, **kwargs):
        """Create a new flavor or instance type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-flavor
        """
        if 'ephemeral' in kwargs:
            kwargs['OS-FLV-EXT-DATA:ephemeral'] = kwargs.pop('ephemeral')
        if 'is_public' in kwargs:
            kwargs['os-flavor-access:is_public'] = kwargs.pop('is_public')

        post_body = json.dumps({'flavor': kwargs})
        resp, body = self.post('flavors', post_body)

        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.create_update_get_flavor_details,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_flavor(self, flavor_id, **kwargs):
        """Uodate the flavor or instance type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#update-flavor-description
        """
        put_body = json.dumps({'flavor': kwargs})
        resp, body = self.put("flavors/%s" % flavor_id, put_body)

        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.create_update_get_flavor_details,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_flavor(self, flavor_id):
        """Delete the given flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-flavor
        """
        resp, body = self.delete("flavors/{0}".format(flavor_id))
        self.validate_response(schema.delete_flavor, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        # Did not use show_flavor(id) for verification as it gives
        # 200 ok even for deleted id. LP #981263
        # we can remove the loop here and use get by ID when bug gets sortedout
        flavors = self.list_flavors(detail=True)['flavors']
        for flavor in flavors:
            if flavor['id'] == id:
                return False
        return True

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'flavor'

    def set_flavor_extra_spec(self, flavor_id, **kwargs):
        """Set extra Specs to the mentioned flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-extra-specs-for-a-flavor
        """
        post_body = json.dumps({'extra_specs': kwargs})
        resp, body = self.post('flavors/%s/os-extra_specs' % flavor_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema_extra_specs.set_get_flavor_extra_specs,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_flavor_extra_specs(self, flavor_id):
        """Get extra Specs details of the mentioned flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-extra-specs-for-a-flavor
        """
        resp, body = self.get('flavors/%s/os-extra_specs' % flavor_id)
        body = json.loads(body)
        self.validate_response(schema_extra_specs.set_get_flavor_extra_specs,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_flavor_extra_spec(self, flavor_id, key):
        """Get extra Specs key-value of the mentioned flavor and key.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#show-an-extra-spec-for-a-flavor
        """
        resp, body = self.get('flavors/%s/os-extra_specs/%s' % (flavor_id,
                                                                key))
        body = json.loads(body)
        self.validate_response(
            schema_extra_specs.set_get_flavor_extra_specs_key,
            resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_flavor_extra_spec(self, flavor_id, key, **kwargs):
        """Update specified extra Specs of the mentioned flavor and key.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#update-an-extra-spec-for-a-flavor
        """
        resp, body = self.put('flavors/%s/os-extra_specs/%s' %
                              (flavor_id, key), json.dumps(kwargs))
        body = json.loads(body)
        self.validate_response(
            schema_extra_specs.set_get_flavor_extra_specs_key,
            resp, body)
        return rest_client.ResponseBody(resp, body)

    def unset_flavor_extra_spec(self, flavor_id, key):  # noqa
        # NOTE: This noqa is for passing T111 check and we cannot rename
        #       to keep backwards compatibility.
        """Unset extra Specs from the mentioned flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-an-extra-spec-for-a-flavor
        """
        resp, body = self.delete('flavors/%s/os-extra_specs/%s' %
                                 (flavor_id, key))
        self.validate_response(schema_extra_specs.unset_flavor_extra_specs,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_flavor_access(self, flavor_id):
        """Get flavor access information given the flavor id.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-flavor-access-information-for-given-flavor
        """
        resp, body = self.get('flavors/%s/os-flavor-access' % flavor_id)
        body = json.loads(body)
        self.validate_response(schema_access.add_remove_list_flavor_access,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def add_flavor_access(self, flavor_id, tenant_id):
        """Add flavor access for the specified tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#add-flavor-access-to-tenant-addtenantaccess-action
        """
        post_body = {
            'addTenantAccess': {
                'tenant': tenant_id
            }
        }
        post_body = json.dumps(post_body)
        resp, body = self.post('flavors/%s/action' % flavor_id, post_body)
        body = json.loads(body)
        self.validate_response(schema_access.add_remove_list_flavor_access,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def remove_flavor_access(self, flavor_id, tenant_id):
        """Remove flavor access from the specified tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#remove-flavor-access-from-tenant-removetenantaccess-action
        """
        post_body = {
            'removeTenantAccess': {
                'tenant': tenant_id
            }
        }
        post_body = json.dumps(post_body)
        resp, body = self.post('flavors/%s/action' % flavor_id, post_body)
        body = json.loads(body)
        self.validate_response(schema_access.add_remove_list_flavor_access,
                               resp, body)
        return rest_client.ResponseBody(resp, body)
