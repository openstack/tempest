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

"""
https://docs.openstack.org/api-ref/identity/v3/index.html#credentials
"""

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class CredentialsClient(rest_client.RestClient):
    api_version = "v3"

    def create_credential(self, **kwargs):
        """Creates a credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-credential
        """
        post_body = json.dumps({'credential': kwargs})
        resp, body = self.post('credentials', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_credential(self, credential_id, **kwargs):
        """Updates a credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-credential
        """
        post_body = json.dumps({'credential': kwargs})
        resp, body = self.patch('credentials/%s' % credential_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_credential(self, credential_id):
        """To GET Details of a credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-credential-details
        """
        resp, body = self.get('credentials/%s' % credential_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_credentials(self, **params):
        """Lists out all the available credentials.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-credentials
        """
        url = 'credentials'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_credential(self, credential_id):
        """Deletes a credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#delete-credential
        """
        resp, body = self.delete('credentials/%s' % credential_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
