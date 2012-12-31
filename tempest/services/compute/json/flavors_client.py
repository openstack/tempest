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
import urllib

from tempest.common.rest_client import RestClient


class FlavorsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FlavorsClientJSON, self).__init__(config, username, password,
                                                auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_flavors(self, params=None):
        url = 'flavors'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['flavors']

    def list_flavors_with_detail(self, params=None):
        url = 'flavors/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['flavors']

    def get_flavor_details(self, flavor_id):
        resp, body = self.get("flavors/%s" % str(flavor_id))
        body = json.loads(body)
        return resp, body['flavor']

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
        resp, body = self.post('flavors', post_body, self.headers)

        body = json.loads(body)
        return resp, body['flavor']

    def delete_flavor(self, flavor_id):
        """Deletes the given flavor."""
        return self.delete("flavors/%s" % str(flavor_id))

    def is_resource_deleted(self, id):
        #Did not use get_flavor_details(id) for verification as it gives
        #200 ok even for deleted id. LP #981263
        #we can remove the loop here and use get by ID when bug gets sortedout
        resp, flavors = self.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['id'] == id:
                return False
        return True
