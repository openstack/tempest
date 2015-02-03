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
from xml.etree import ElementTree as etree

from tempest.common import service_client


class AccountClient(service_client.ServiceClient):

    def create_account(self, data=None,
                       params=None,
                       metadata=None,
                       remove_metadata=None,
                       metadata_prefix='X-Account-Meta-',
                       remove_metadata_prefix='X-Remove-Account-Meta-'):
        """Create an account."""
        if metadata is None:
            metadata = {}
        if remove_metadata is None:
            remove_metadata = {}
        url = ''
        if params:
            url += '?%s' % urllib.urlencode(params)

        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]
        for key in remove_metadata:
            headers[remove_metadata_prefix + key] = remove_metadata[key]

        resp, body = self.put(url, data, headers)
        self.expected_success(200, resp.status)
        return resp, body

    def delete_account(self, data=None, params=None):
        """Delete an account."""
        url = ''
        if params:
            url = '?%s%s' % (url, urllib.urlencode(params))

        resp, body = self.delete(url, headers={}, body=data)
        self.expected_success(200, resp.status)
        return resp, body

    def list_account_metadata(self):
        """
        HEAD on the storage URL
        Returns all account metadata headers
        """
        resp, body = self.head('')
        self.expected_success(204, resp.status)
        return resp, body

    def create_account_metadata(self, metadata,
                                metadata_prefix='X-Account-Meta-',
                                data=None, params=None):
        """Creates an account metadata entry."""
        headers = {}
        if metadata:
            for key in metadata:
                headers[metadata_prefix + key] = metadata[key]

        url = ''
        if params:
            url = '?%s%s' % (url, urllib.urlencode(params))

        resp, body = self.post(url, headers=headers, body=data)
        self.expected_success([200, 204], resp.status)
        return resp, body

    def delete_account_metadata(self, metadata,
                                metadata_prefix='X-Remove-Account-Meta-'):
        """
        Deletes an account metadata entry.
        """

        headers = {}
        for item in metadata:
            headers[metadata_prefix + item] = metadata[item]
        resp, body = self.post('', headers=headers, body=None)
        self.expected_success(204, resp.status)
        return resp, body

    def create_and_delete_account_metadata(
            self,
            create_metadata=None,
            delete_metadata=None,
            create_metadata_prefix='X-Account-Meta-',
            delete_metadata_prefix='X-Remove-Account-Meta-'):
        """
        Creates and deletes an account metadata entry.
        """
        headers = {}
        for key in create_metadata:
            headers[create_metadata_prefix + key] = create_metadata[key]
        for key in delete_metadata:
            headers[delete_metadata_prefix + key] = delete_metadata[key]

        resp, body = self.post('', headers=headers, body=None)
        self.expected_success(204, resp.status)
        return resp, body

    def list_account_containers(self, params=None):
        """
        GET on the (base) storage URL
        Given valid X-Auth-Token, returns a list of all containers for the
        account.

        Optional Arguments:
        limit=[integer value N]
            Limits the number of results to at most N values
            DEFAULT:  10,000

        marker=[string value X]
            Given string value X, return object names greater in value
            than the specified marker.
            DEFAULT: No Marker

        format=[string value, either 'json' or 'xml']
            Specify either json or xml to return the respective serialized
            response.
            DEFAULT:  Python-List returned in response body
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

    def list_extensions(self):
        self.skip_path()
        try:
            resp, body = self.get('info')
        finally:
            self.reset_path()
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return resp, body
