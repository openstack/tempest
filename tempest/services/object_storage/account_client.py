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

from tempest.common import http
from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class AccountClient(rest_client.RestClient):
    def __init__(self, auth_provider):
        super(AccountClient, self).__init__(auth_provider)
        self.service = CONF.object_storage.catalog_type

    def create_account(self, data=None,
                       params=None,
                       metadata={},
                       remove_metadata={},
                       metadata_prefix='X-Account-Meta-',
                       remove_metadata_prefix='X-Remove-Account-Meta-'):
        """Create an account."""
        url = ''
        if params:
            url += '?%s' % urllib.urlencode(params)

        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]
        for key in remove_metadata:
            headers[remove_metadata_prefix + key] = remove_metadata[key]

        resp, body = self.put(url, data, headers)
        return resp, body

    def delete_account(self, data=None, params=None):
        """Delete an account."""
        url = ''
        if params:
            if 'bulk-delete' in params:
                url += 'bulk-delete&'
            url = '?%s%s' % (url, urllib.urlencode(params))

        resp, body = self.delete(url, headers={}, body=data)
        return resp, body

    def list_account_metadata(self):
        """
        HEAD on the storage URL
        Returns all account metadata headers
        """
        resp, body = self.head('')
        return resp, body

    def create_account_metadata(self, metadata,
                                metadata_prefix='X-Account-Meta-'):
        """Creates an account metadata entry."""
        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]

        resp, body = self.post('', headers=headers, body=None)
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
        return resp, body

    def list_extensions(self):
        self.skip_path()
        try:
            resp, body = self.get('info')
        finally:
            self.reset_path()
        body = json.loads(body)
        return resp, body


class AccountClientCustomizedHeader(rest_client.RestClient):

    # TODO(andreaf) This class is now redundant, to be removed in next patch

    def __init__(self, auth_provider):
        super(AccountClientCustomizedHeader, self).__init__(
            auth_provider)
        # Overwrites json-specific header encoding in rest_client.RestClient
        self.service = CONF.object_storage.catalog_type
        self.format = 'json'

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        """A simple HTTP request interface."""
        self.http_obj = http.ClosingHttp()
        if headers is None:
            headers = {}
        elif extra_headers:
            try:
                headers.update(self.get_headers())
            except (ValueError, TypeError):
                headers = {}

        # Authorize the request
        req_url, req_headers, req_body = self.auth_provider.auth_request(
            method=method, url=url, headers=headers, body=body,
            filters=self.filters
        )
        # use original body
        resp, resp_body = self.http_obj.request(req_url, method,
                                                headers=req_headers,
                                                body=req_body)
        self._log_request(method, req_url, resp)

        if resp.status == 401 or resp.status == 403:
            raise exceptions.Unauthorized()

        return resp, resp_body

    def list_account_containers(self, params=None, metadata=None):
        """
        GET on the (base) storage URL
        Given a valid X-Auth-Token, returns a list of all containers for the
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

        url = '?format=%s' % self.format
        if params:
            url += '&%s' + urllib.urlencode(params)

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        resp, body = self.get(url, headers=headers)
        return resp, body
