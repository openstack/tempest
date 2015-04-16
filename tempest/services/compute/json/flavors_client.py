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

from tempest.api_schema.response.compute import flavors_access as schema_access
from tempest.api_schema.response.compute import flavors_extra_specs \
    as schema_extra_specs
from tempest.api_schema.response.compute.v2_1 import flavors as schema
from tempest.common import service_client


class FlavorsClientJSON(service_client.ServiceClient):

    def list_flavors(self, params=None):
        url = 'flavors'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_flavors, resp, body)
        return service_client.ResponseBodyList(resp, body['flavors'])

    def list_flavors_with_detail(self, params=None):
        url = 'flavors/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_flavors_details, resp, body)
        return service_client.ResponseBodyList(resp, body['flavors'])

    def get_flavor_details(self, flavor_id):
        resp, body = self.get("flavors/%s" % str(flavor_id))
        body = json.loads(body)
        self.validate_response(schema.create_get_flavor_details, resp, body)
        return service_client.ResponseBody(resp, body['flavor'])

    def create_flavor(self, name, ram, vcpus, disk, flavor_id, **kwargs):
        """Creates a new flavor or instance type."""
        post_body = {
            'name': name,
            'ram': ram,
            'vcpus': vcpus,
            'disk': disk,
            'id': flavor_id,
        }
        if kwargs.get('ephemeral'):
            post_body['OS-FLV-EXT-DATA:ephemeral'] = kwargs.get('ephemeral')
        if kwargs.get('swap'):
            post_body['swap'] = kwargs.get('swap')
        if kwargs.get('rxtx'):
            post_body['rxtx_factor'] = kwargs.get('rxtx')
        if kwargs.get('is_public'):
            post_body['os-flavor-access:is_public'] = kwargs.get('is_public')
        post_body = json.dumps({'flavor': post_body})
        resp, body = self.post('flavors', post_body)

        body = json.loads(body)
        self.validate_response(schema.create_get_flavor_details, resp, body)
        return service_client.ResponseBody(resp, body['flavor'])

    def delete_flavor(self, flavor_id):
        """Deletes the given flavor."""
        resp, body = self.delete("flavors/{0}".format(flavor_id))
        self.validate_response(schema.delete_flavor, resp, body)
        return service_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        # Did not use get_flavor_details(id) for verification as it gives
        # 200 ok even for deleted id. LP #981263
        # we can remove the loop here and use get by ID when bug gets sortedout
        flavors = self.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['id'] == id:
                return False
        return True

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'flavor'

    def set_flavor_extra_spec(self, flavor_id, specs):
        """Sets extra Specs to the mentioned flavor."""
        post_body = json.dumps({'extra_specs': specs})
        resp, body = self.post('flavors/%s/os-extra_specs' % flavor_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema_extra_specs.flavor_extra_specs,
                               resp, body)
        return service_client.ResponseBody(resp, body['extra_specs'])

    def get_flavor_extra_spec(self, flavor_id):
        """Gets extra Specs details of the mentioned flavor."""
        resp, body = self.get('flavors/%s/os-extra_specs' % flavor_id)
        body = json.loads(body)
        self.validate_response(schema_extra_specs.flavor_extra_specs,
                               resp, body)
        return service_client.ResponseBody(resp, body['extra_specs'])

    def get_flavor_extra_spec_with_key(self, flavor_id, key):
        """Gets extra Specs key-value of the mentioned flavor and key."""
        resp, body = self.get('flavors/%s/os-extra_specs/%s' % (str(flavor_id),
                              key))
        body = json.loads(body)
        self.validate_response(schema_extra_specs.flavor_extra_specs_key,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def update_flavor_extra_spec(self, flavor_id, key, **kwargs):
        """Update specified extra Specs of the mentioned flavor and key."""
        resp, body = self.put('flavors/%s/os-extra_specs/%s' %
                              (flavor_id, key), json.dumps(kwargs))
        body = json.loads(body)
        self.validate_response(schema_extra_specs.flavor_extra_specs_key,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def unset_flavor_extra_spec(self, flavor_id, key):
        """Unsets extra Specs from the mentioned flavor."""
        resp, body = self.delete('flavors/%s/os-extra_specs/%s' %
                                 (str(flavor_id), key))
        self.validate_response(schema.unset_flavor_extra_specs, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_flavor_access(self, flavor_id):
        """Gets flavor access information given the flavor id."""
        resp, body = self.get('flavors/%s/os-flavor-access' % flavor_id)
        body = json.loads(body)
        self.validate_response(schema_access.add_remove_list_flavor_access,
                               resp, body)
        return service_client.ResponseBodyList(resp, body['flavor_access'])

    def add_flavor_access(self, flavor_id, tenant_id):
        """Add flavor access for the specified tenant."""
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
        return service_client.ResponseBodyList(resp, body['flavor_access'])

    def remove_flavor_access(self, flavor_id, tenant_id):
        """Remove flavor access from the specified tenant."""
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
        return service_client.ResponseBody(resp, body['flavor_access'])
