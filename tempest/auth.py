# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import copy
import exceptions
import re
import urlparse

from datetime import datetime
from tempest import config
from tempest.services.identity.json import identity_client as json_id
from tempest.services.identity.v3.json import identity_client as json_v3id
from tempest.services.identity.v3.xml import identity_client as xml_v3id
from tempest.services.identity.xml import identity_client as xml_id

from tempest.openstack.common import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


class AuthProvider(object):
    """
    Provide authentication
    """

    def __init__(self, credentials, client_type='tempest',
                 interface=None):
        """
        :param credentials: credentials for authentication
        :param client_type: 'tempest' or 'official'
        :param interface: 'json' or 'xml'. Applicable for tempest client only
        """
        if self.check_credentials(credentials):
            self.credentials = credentials
        else:
            raise TypeError("Invalid credentials")
        self.credentials = credentials
        self.client_type = client_type
        self.interface = interface
        if self.client_type == 'tempest' and self.interface is None:
            self.interface = 'json'
        self.cache = None
        self.alt_auth_data = None
        self.alt_part = None

    def __str__(self):
        return "Creds :{creds}, client type: {client_type}, interface: " \
               "{interface}, cached auth data: {cache}".format(
                   creds=self.credentials, client_type=self.client_type,
                   interface=self.interface, cache=self.cache
               )

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        """
        Decorate request with authentication data
        """
        raise NotImplementedError

    def _get_auth(self):
        raise NotImplementedError

    @classmethod
    def check_credentials(cls, credentials):
        """
        Verify credentials are valid. Subclasses can do a better check.
        """
        return isinstance(credentials, dict)

    @property
    def auth_data(self):
        if self.cache is None or self.is_expired(self.cache):
            self.cache = self._get_auth()
        return self.cache

    @auth_data.deleter
    def auth_data(self):
        self.clear_auth()

    def clear_auth(self):
        """
        Can be called to clear the access cache so that next request
        will fetch a new token and base_url.
        """
        self.cache = None

    def is_expired(self, auth_data):
        raise NotImplementedError

    def auth_request(self, method, url, headers=None, body=None, filters=None):
        """
        Obtains auth data and decorates a request with that.
        :param method: HTTP method of the request
        :param url: relative URL of the request (path)
        :param headers: HTTP headers of the request
        :param body: HTTP body in case of POST / PUT
        :param filters: select a base URL out of the catalog
        :returns a Tuple (url, headers, body)
        """
        orig_req = dict(url=url, headers=headers, body=body)

        auth_url, auth_headers, auth_body = self._decorate_request(
            filters, method, url, headers, body)
        auth_req = dict(url=auth_url, headers=auth_headers, body=auth_body)

        # Overwrite part if the request if it has been requested
        if self.alt_part is not None:
            if self.alt_auth_data is not None:
                alt_url, alt_headers, alt_body = self._decorate_request(
                    filters, method, url, headers, body,
                    auth_data=self.alt_auth_data)
                alt_auth_req = dict(url=alt_url, headers=alt_headers,
                                    body=alt_body)
                auth_req[self.alt_part] = alt_auth_req[self.alt_part]

            else:
                # If alt auth data is None, skip auth in the requested part
                auth_req[self.alt_part] = orig_req[self.alt_part]

            # Next auth request will be normal, unless otherwise requested
            self.reset_alt_auth_data()

        return auth_req['url'], auth_req['headers'], auth_req['body']

    def reset_alt_auth_data(self):
        """
        Configure auth provider to provide valid authentication data
        """
        self.alt_part = None
        self.alt_auth_data = None

    def set_alt_auth_data(self, request_part, auth_data):
        """
        Configure auth provider to provide alt authentication data
        on a part of the *next* auth_request. If credentials are None,
        set invalid data.
        :param request_part: request part to contain invalid auth: url,
                             headers, body
        :param auth_data: alternative auth_data from which to get the
                          invalid data to be injected
        """
        self.alt_part = request_part
        self.alt_auth_data = auth_data

    def base_url(self, filters, auth_data=None):
        """
        Extracts the base_url based on provided filters
        """
        raise NotImplementedError


class KeystoneAuthProvider(AuthProvider):

    def __init__(self, credentials, client_type='tempest', interface=None):
        super(KeystoneAuthProvider, self).__init__(credentials, client_type,
                                                   interface)
        self.auth_client = self._auth_client()

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        if auth_data is None:
            auth_data = self.auth_data
        token, _ = auth_data
        base_url = self.base_url(filters=filters, auth_data=auth_data)
        # build authenticated request
        # returns new request, it does not touch the original values
        _headers = copy.deepcopy(headers) if headers is not None else {}
        _headers['X-Auth-Token'] = token
        if url is None or url == "":
            _url = base_url
        else:
            # Join base URL and url, and remove multiple contiguous slashes
            _url = "/".join([base_url, url])
            parts = [x for x in urlparse.urlparse(_url)]
            parts[2] = re.sub("/{2,}", "/", parts[2])
            _url = urlparse.urlunparse(parts)
        # no change to method or body
        return _url, _headers, body

    def _auth_client(self):
        raise NotImplementedError

    def _auth_params(self):
        raise NotImplementedError

    def _get_auth(self):
        # Bypasses the cache
        if self.client_type == 'tempest':
            auth_func = getattr(self.auth_client, 'get_token')
            auth_params = self._auth_params()

            # returns token, auth_data
            token, auth_data = auth_func(**auth_params)
            return token, auth_data
        else:
            raise NotImplementedError

    def get_token(self):
        return self.auth_data[0]


class KeystoneV2AuthProvider(KeystoneAuthProvider):

    EXPIRY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    @classmethod
    def check_credentials(cls, credentials, scoped=True):
        # tenant_name is optional if not scoped
        valid = super(KeystoneV2AuthProvider, cls).check_credentials(
            credentials) and 'username' in credentials and \
            'password' in credentials
        if scoped:
            valid = valid and 'tenant_name' in credentials
        return valid

    def _auth_client(self):
        if self.client_type == 'tempest':
            if self.interface == 'json':
                return json_id.TokenClientJSON()
            else:
                return xml_id.TokenClientXML()
        else:
            raise NotImplementedError

    def _auth_params(self):
        if self.client_type == 'tempest':
            return dict(
                user=self.credentials['username'],
                password=self.credentials['password'],
                tenant=self.credentials.get('tenant_name', None),
                auth_data=True)
        else:
            raise NotImplementedError

    def base_url(self, filters, auth_data=None):
        """
        Filters can be:
        - service: compute, image, etc
        - region: the service region
        - endpoint_type: adminURL, publicURL, internalURL
        - api_version: replace catalog version with this
        - skip_path: take just the base URL
        """
        if auth_data is None:
            auth_data = self.auth_data
        token, _auth_data = auth_data
        service = filters.get('service')
        region = filters.get('region')
        endpoint_type = filters.get('endpoint_type', 'publicURL')

        if service is None:
            raise exceptions.EndpointNotFound("No service provided")

        _base_url = None
        for ep in _auth_data['serviceCatalog']:
            if ep["type"] == service:
                for _ep in ep['endpoints']:
                    if region is not None and _ep['region'] == region:
                        _base_url = _ep.get(endpoint_type)
                if not _base_url:
                    # No region matching, use the first
                    _base_url = ep['endpoints'][0].get(endpoint_type)
                break
        if _base_url is None:
            raise exceptions.EndpointNotFound(service)

        parts = urlparse.urlparse(_base_url)
        if filters.get('api_version', None) is not None:
            path = "/" + filters['api_version']
            noversion_path = "/".join(parts.path.split("/")[2:])
            if noversion_path != "":
                path += "/" + noversion_path
            _base_url = _base_url.replace(parts.path, path)
        if filters.get('skip_path', None) is not None:
            _base_url = _base_url.replace(parts.path, "/")

        return _base_url

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = datetime.strptime(access['token']['expires'],
                                   self.EXPIRY_DATE_FORMAT)
        return expiry <= datetime.now()


class KeystoneV3AuthProvider(KeystoneAuthProvider):

    EXPIRY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    @classmethod
    def check_credentials(cls, credentials, scoped=True):
        # tenant_name is optional if not scoped
        valid = super(KeystoneV3AuthProvider, cls).check_credentials(
            credentials) and 'username' in credentials and \
            'password' in credentials and 'domain_name' in credentials
        if scoped:
            valid = valid and 'tenant_name' in credentials
        return valid

    def _auth_client(self):
        if self.client_type == 'tempest':
            if self.interface == 'json':
                return json_v3id.V3TokenClientJSON()
            else:
                return xml_v3id.V3TokenClientXML()
        else:
            raise NotImplementedError

    def _auth_params(self):
        if self.client_type == 'tempest':
            return dict(
                user=self.credentials['username'],
                password=self.credentials['password'],
                tenant=self.credentials.get('tenant_name', None),
                domain=self.credentials['domain_name'],
                auth_data=True)
        else:
            raise NotImplementedError

    def base_url(self, filters, auth_data=None):
        """
        Filters can be:
        - service: compute, image, etc
        - region: the service region
        - endpoint_type: adminURL, publicURL, internalURL
        - api_version: replace catalog version with this
        - skip_path: take just the base URL
        """
        if auth_data is None:
            auth_data = self.auth_data
        token, _auth_data = auth_data
        service = filters.get('service')
        region = filters.get('region')
        endpoint_type = filters.get('endpoint_type', 'public')

        if service is None:
            raise exceptions.EndpointNotFound("No service provided")

        if 'URL' in endpoint_type:
            endpoint_type = endpoint_type.replace('URL', '')
        _base_url = None
        catalog = _auth_data['catalog']
        # Select entries with matching service type
        service_catalog = [ep for ep in catalog if ep['type'] == service]
        if len(service_catalog) > 0:
            service_catalog = service_catalog[0]['endpoints']
        else:
            # No matching service
            raise exceptions.EndpointNotFound(service)
        # Filter by endpoint type (interface)
        filtered_catalog = [ep for ep in service_catalog if
                            ep['interface'] == endpoint_type]
        if len(filtered_catalog) == 0:
            # No matching type, keep all and try matching by region at least
            filtered_catalog = service_catalog
        # Filter by region
        filtered_catalog = [ep for ep in filtered_catalog if
                            ep['region'] == region]
        if len(filtered_catalog) == 0:
            # No matching region, take the first endpoint
            filtered_catalog = [service_catalog[0]]
        # There should be only one match. If not take the first.
        _base_url = filtered_catalog[0].get('url', None)
        if _base_url is None:
                raise exceptions.EndpointNotFound(service)

        parts = urlparse.urlparse(_base_url)
        if filters.get('api_version', None) is not None:
            path = "/" + filters['api_version']
            noversion_path = "/".join(parts.path.split("/")[2:])
            if noversion_path != "":
                path += noversion_path
            _base_url = _base_url.replace(parts.path, path)
        if filters.get('skip_path', None) is not None:
            _base_url = _base_url.replace(parts.path, "/")

        return _base_url

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = datetime.strptime(access['expires_at'],
                                   self.EXPIRY_DATE_FORMAT)
        return expiry <= datetime.now()
