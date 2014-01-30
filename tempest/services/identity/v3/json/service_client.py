# Copyright 2013 OpenStack Foundation
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
from urlparse import urlparse

from tempest.common.rest_client import RestClient
from tempest import config

CONF = config.CONF


class ServiceClientJSON(RestClient):

    def __init__(self, username, password, auth_url, tenant_name=None):
        super(ServiceClientJSON, self).__init__(username, password,
                                                auth_url, tenant_name)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(ServiceClientJSON, self).request(method, url,
                                                      headers=headers,
                                                      body=body)

    def update_service(self, service_id, **kwargs):
        """Updates a service."""
        resp, body = self.get_service(service_id)
        name = kwargs.get('name', body['name'])
        type = kwargs.get('type', body['type'])
        desc = kwargs.get('description', body['description'])
        patch_body = {
            'description': desc,
            'type': type,
            'name': name
        }
        patch_body = json.dumps({'service': patch_body})
        resp, body = self.patch('services/%s' % service_id,
                                patch_body, self.headers)
        body = json.loads(body)
        return resp, body['service']

    def get_service(self, service_id):
        """Get Service."""
        url = 'services/%s' % service_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['service']
