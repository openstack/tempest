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

from xml.etree import ElementTree as etree

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class AccountClient(rest_client.RestClient):

    def create_update_or_delete_account_metadata(
            self,
            create_update_metadata=None,
            delete_metadata=None,
            create_update_metadata_prefix='X-Account-Meta-',
            delete_metadata_prefix='X-Remove-Account-Meta-'):
        """Creates, Updates or deletes an account metadata entry.

        Account Metadata can be created, updated or deleted based on
        metadata header or value. For detailed info, please refer to the
        official API reference:
        https://developer.openstack.org/api-ref/object-store/#create-update-or-delete-account-metadata
        """
        headers = {}
        if create_update_metadata:
            for key in create_update_metadata:
                metadata_header_name = create_update_metadata_prefix + key
                headers[metadata_header_name] = create_update_metadata[key]
        if delete_metadata:
            for key in delete_metadata:
                headers[delete_metadata_prefix + key] = delete_metadata[key]

        resp, body = self.post('', headers=headers, body=None)
        self.expected_success([200, 204], resp.status)
        return resp, body

    def list_account_metadata(self):
        """List all account metadata."""
        resp, body = self.head('')
        self.expected_success(204, resp.status)
        return resp, body

    def list_account_containers(self, params=None):
        """List all containers for the account.

        Given valid X-Auth-Token, returns a list of all containers for the
        account.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/object-store/#show-account-details-and-list-containers
        """
        url = '?%s' % urllib.urlencode(params) if params else ''

        resp, body = self.get(url, headers={})
        if params and params.get('format') == 'json':
            body = json.loads(body)
        elif params and params.get('format') == 'xml':
            body = etree.fromstring(body)
        else:
            body = body.strip().splitlines()
        self.expected_success([200, 204], resp.status)
        return resp, body
