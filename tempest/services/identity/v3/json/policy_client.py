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


class PolicyClientJSON(RestClient):

    def __init__(self, username, password, auth_url, tenant_name=None):
        super(PolicyClientJSON, self).__init__(username, password,
                                               auth_url, tenant_name)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(PolicyClientJSON, self).request(method, url,
                                                     headers=headers,
                                                     body=body)

    def create_policy(self, blob, type):
        """Creates a Policy."""
        post_body = {
            "blob": blob,
            "type": type
        }
        post_body = json.dumps({'policy': post_body})
        resp, body = self.post('policies', post_body, self.headers)
        body = json.loads(body)
        return resp, body['policy']

    def list_policies(self):
        """Lists the policies."""
        resp, body = self.get('policies')
        body = json.loads(body)
        return resp, body['policies']

    def get_policy(self, policy_id):
        """Lists out the given policy."""
        url = 'policies/%s' % policy_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['policy']

    def update_policy(self, policy_id, **kwargs):
        """Updates a policy."""
        resp, body = self.get_policy(policy_id)
        type = kwargs.get('type')
        post_body = {
            'type': type
        }
        post_body = json.dumps({'policy': post_body})
        url = 'policies/%s' % policy_id
        resp, body = self.patch(url, post_body,
                                self.headers)
        body = json.loads(body)
        return resp, body['policy']

    def delete_policy(self, policy_id):
        """Deletes the policy."""
        url = "policies/%s" % policy_id
        return self.delete(url)
