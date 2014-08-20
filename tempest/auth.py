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

import abc
import copy
import datetime
import exceptions
import re
import urlparse

import six

from tempest import config
from tempest.openstack.common import log as logging
from tempest.services.identity.json import identity_client as json_id
from tempest.services.identity.v3.json import identity_client as json_v3id
from tempest.services.identity.v3.xml import identity_client as xml_v3id
from tempest.services.identity.xml import identity_client as xml_id


CONF = config.CONF
LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
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
        credentials = self._convert_credentials(credentials)
        if self.check_credentials(credentials):
            self.credentials = credentials
        else:
            raise TypeError("Invalid credentials")
        self.client_type = client_type
        self.interface = interface
        if self.client_type == 'tempest' and self.interface is None:
            self.interface = 'json'
        self.cache = None
        self.alt_auth_data = None
        self.alt_part = None

    def _convert_credentials(self, credentials):
        # Support dict credentials for backwards compatibility
        if isinstance(credentials, dict):
            return get_credentials(**credentials)
        else:
            return credentials

    def __str__(self):
        return "Creds :{creds}, client type: {client_type}, interface: " \
               "{interface}, cached auth data: {cache}".format(
                   creds=self.credentials, client_type=self.client_type,
                   interface=self.interface, cache=self.cache
               )

    @abc.abstractmethod
    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        """
        Decorate request with authentication data
        """
        return

    @abc.abstractmethod
    def _get_auth(self):
        return

    @abc.abstractmethod
    def _fill_credentials(self, auth_data_body):
        return

    def fill_credentials(self):
        """
        Fill credentials object with data from auth
        """
        auth_data = self.get_auth()
        self._fill_credentials(auth_data[1])
        return self.credentials

    @classmethod
    def check_credentials(cls, credentials):
        """
        Verify credentials are valid.
        """
        return isinstance(credentials, Credentials) and credentials.is_valid()

    @property
    def auth_data(self):
        return self.get_auth()

    @auth_data.deleter
    def auth_data(self):
        self.clear_auth()

    def get_auth(self):
        """
        Returns auth from cache if available, else auth first
        """
        if self.cache is None or self.is_expired(self.cache):
            self.set_auth()
        return self.cache

    def set_auth(self):
        """
        Forces setting auth, ignores cache if it exists.
        Refills credentials
        """
        self.cache = self._get_auth()
        self._fill_credentials(self.cache[1])

    def clear_auth(self):
        """
        Can be called to clear the access cache so that next request
        will fetch a new token and base_url.
        """
        self.cache = None
        self.credentials.reset()

    @abc.abstractmethod
    def is_expired(self, auth_data):
        return

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

    @abc.abstractmethod
    def base_url(self, filters, auth_data=None):
        """
        Extracts the base_url based on provided filters
        """
        return


class KeystoneAuthProvider(AuthProvider):

    token_expiry_threshold = datetime.timedelta(seconds=60)

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
        _headers['X-Auth-Token'] = str(token)
        if url is None or url == "":
            _url = base_url
        else:
            # Join base URL and url, and remove multiple contiguous slashes
            _url = "/".join([base_url, url])
            parts = [x for x in urlparse.urlparse(_url)]
            parts[2] = re.sub("/{2,}", "/", parts[2])
            _url = urlparse.urlunparse(parts)
        # no change to method or body
        return str(_url), _headers, body

    @abc.abstractmethod
    def _auth_client(self):
        return

    @abc.abstractmethod
    def _auth_params(self):
        return

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
                user=self.credentials.username,
                password=self.credentials.password,
                tenant=self.credentials.tenant_name,
                auth_data=True)
        else:
            raise NotImplementedError

    def _fill_credentials(self, auth_data_body):
        tenant = auth_data_body['token']['tenant']
        user = auth_data_body['user']
        if self.credentials.tenant_name is None:
            self.credentials.tenant_name = tenant['name']
        if self.credentials.tenant_id is None:
            self.credentials.tenant_id = tenant['id']
        if self.credentials.username is None:
            self.credentials.username = user['name']
        if self.credentials.user_id is None:
            self.credentials.user_id = user['id']

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
        if filters.get('skip_path', None) is not None and parts.path != '':
            _base_url = _base_url.replace(parts.path, "/")

        return _base_url

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = datetime.datetime.strptime(access['token']['expires'],
                                            self.EXPIRY_DATE_FORMAT)
        return expiry - self.token_expiry_threshold <= \
            datetime.datetime.utcnow()


class KeystoneV3AuthProvider(KeystoneAuthProvider):

    EXPIRY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

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
                user=self.credentials.username,
                password=self.credentials.password,
                tenant=self.credentials.tenant_name,
                domain=self.credentials.user_domain_name,
                auth_data=True)
        else:
            raise NotImplementedError

    def _fill_credentials(self, auth_data_body):
        # project or domain, depending on the scope
        project = auth_data_body.get('project', None)
        domain = auth_data_body.get('domain', None)
        # user is always there
        user = auth_data_body['user']
        # Set project fields
        if project is not None:
            if self.credentials.project_name is None:
                self.credentials.project_name = project['name']
            if self.credentials.project_id is None:
                self.credentials.project_id = project['id']
            if self.credentials.project_domain_id is None:
                self.credentials.project_domain_id = project['domain']['id']
            if self.credentials.project_domain_name is None:
                self.credentials.project_domain_name = \
                    project['domain']['name']
        # Set domain fields
        if domain is not None:
            if self.credentials.domain_id is None:
                self.credentials.domain_id = domain['id']
            if self.credentials.domain_name is None:
                self.credentials.domain_name = domain['name']
        # Set user fields
        if self.credentials.username is None:
            self.credentials.username = user['name']
        if self.credentials.user_id is None:
            self.credentials.user_id = user['id']
        if self.credentials.user_domain_id is None:
            self.credentials.user_domain_id = user['domain']['id']
        if self.credentials.user_domain_name is None:
            self.credentials.user_domain_name = user['domain']['name']

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
                path += "/" + noversion_path
            _base_url = _base_url.replace(parts.path, path)
        if filters.get('skip_path', None) is not None:
            _base_url = _base_url.replace(parts.path, "/")

        return _base_url

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = datetime.datetime.strptime(access['expires_at'],
                                            self.EXPIRY_DATE_FORMAT)
        return expiry - self.token_expiry_threshold <= \
            datetime.datetime.utcnow()


def get_default_credentials(credential_type, fill_in=True):
    """
    Returns configured credentials of the specified type
    based on the configured auth_version
    """
    return get_credentials(fill_in=fill_in, credential_type=credential_type)


def get_credentials(credential_type=None, fill_in=True, **kwargs):
    """
    Builds a credentials object based on the configured auth_version

    :param credential_type (string): requests credentials from tempest
           configuration file. Valid values are defined in
           Credentials.TYPE.
    :param kwargs (dict): take into account only if credential_type is
           not specified or None. Dict of credential key/value pairs

    Examples:

        Returns credentials from the provided parameters:
        >>> get_credentials(username='foo', password='bar')

        Returns credentials from tempest configuration:
        >>> get_credentials(credential_type='user')
    """
    if CONF.identity.auth_version == 'v2':
        credential_class = KeystoneV2Credentials
        auth_provider_class = KeystoneV2AuthProvider
    elif CONF.identity.auth_version == 'v3':
        credential_class = KeystoneV3Credentials
        auth_provider_class = KeystoneV3AuthProvider
    else:
        raise exceptions.InvalidConfiguration('Unsupported auth version')
    if credential_type is not None:
        creds = credential_class.get_default(credential_type)
    else:
        creds = credential_class(**kwargs)
    # Fill in the credentials fields that were not specified
    if fill_in:
        auth_provider = auth_provider_class(creds)
        creds = auth_provider.fill_credentials()
    return creds


class Credentials(object):
    """
    Set of credentials for accessing OpenStack services

    ATTRIBUTES: list of valid class attributes representing credentials.

    TYPES: types of credentials available in the configuration file.
           For each key there's a tuple (section, prefix) to match the
           configuration options.
    """

    ATTRIBUTES = []
    TYPES = {
        'identity_admin': ('identity', 'admin'),
        'compute_admin': ('compute_admin', None),
        'user': ('identity', None),
        'alt_user': ('identity', 'alt')
    }

    def __init__(self, **kwargs):
        """
        Enforce the available attributes at init time (only).
        Additional attributes can still be set afterwards if tests need
        to do so.
        """
        self._initial = kwargs
        self._apply_credentials(kwargs)

    def _apply_credentials(self, attr):
        for key in attr.keys():
            if key in self.ATTRIBUTES:
                setattr(self, key, attr[key])
            else:
                raise exceptions.InvalidCredentials

    def __str__(self):
        """
        Represent only attributes included in self.ATTRIBUTES
        """
        _repr = dict((k, getattr(self, k)) for k in self.ATTRIBUTES)
        return str(_repr)

    def __eq__(self, other):
        """
        Credentials are equal if attributes in self.ATTRIBUTES are equal
        """
        return str(self) == str(other)

    def __getattr__(self, key):
        # If an attribute is set, __getattr__ is not invoked
        # If an attribute is not set, and it is a known one, return None
        if key in self.ATTRIBUTES:
            return None
        else:
            raise AttributeError

    def __delitem__(self, key):
        # For backwards compatibility, support dict behaviour
        if key in self.ATTRIBUTES:
            delattr(self, key)
        else:
            raise AttributeError

    def get(self, item, default):
        # In this patch act as dict for backward compatibility
        try:
            return getattr(self, item)
        except AttributeError:
            return default

    @classmethod
    def get_default(cls, credentials_type):
        if credentials_type not in cls.TYPES:
            raise exceptions.InvalidCredentials()
        creds = cls._get_default(credentials_type)
        if not creds.is_valid():
            raise exceptions.InvalidConfiguration()
        return creds

    @classmethod
    def _get_default(cls, credentials_type):
        raise NotImplementedError

    def is_valid(self):
        raise NotImplementedError

    def reset(self):
        # First delete all known attributes
        for key in self.ATTRIBUTES:
            if getattr(self, key) is not None:
                delattr(self, key)
        # Then re-apply initial setup
        self._apply_credentials(self._initial)


class KeystoneV2Credentials(Credentials):

    CONF_ATTRIBUTES = ['username', 'password', 'tenant_name']
    ATTRIBUTES = ['user_id', 'tenant_id']
    ATTRIBUTES.extend(CONF_ATTRIBUTES)

    @classmethod
    def _get_default(cls, credentials_type='user'):
        params = {}
        section, prefix = cls.TYPES[credentials_type]
        for attr in cls.CONF_ATTRIBUTES:
            _section = getattr(CONF, section)
            if prefix is None:
                params[attr] = getattr(_section, attr)
            else:
                params[attr] = getattr(_section, prefix + "_" + attr)
        return cls(**params)

    def is_valid(self):
        """
        Minimum set of valid credentials, are username and password.
        Tenant is optional.
        """
        return None not in (self.username, self.password)


class KeystoneV3Credentials(KeystoneV2Credentials):
    """
    Credentials suitable for the Keystone Identity V3 API
    """

    CONF_ATTRIBUTES = ['domain_name', 'password', 'tenant_name', 'username']
    ATTRIBUTES = ['project_domain_id', 'project_domain_name', 'project_id',
                  'project_name', 'tenant_id', 'tenant_name', 'user_domain_id',
                  'user_domain_name', 'user_id']
    ATTRIBUTES.extend(CONF_ATTRIBUTES)

    def __init__(self, **kwargs):
        """
        If domain is not specified, load the one configured for the
        identity manager.
        """
        domain_fields = set(x for x in self.ATTRIBUTES if 'domain' in x)
        if not domain_fields.intersection(kwargs.keys()):
            kwargs['user_domain_name'] = CONF.identity.admin_domain_name
        super(KeystoneV3Credentials, self).__init__(**kwargs)

    def __setattr__(self, key, value):
        parent = super(KeystoneV3Credentials, self)
        # for tenant_* set both project and tenant
        if key == 'tenant_id':
            parent.__setattr__('project_id', value)
        elif key == 'tenant_name':
            parent.__setattr__('project_name', value)
        # for project_* set both project and tenant
        if key == 'project_id':
            parent.__setattr__('tenant_id', value)
        elif key == 'project_name':
            parent.__setattr__('tenant_name', value)
        # for *_domain_* set both user and project if not set yet
        if key == 'user_domain_id':
            if self.project_domain_id is None:
                parent.__setattr__('project_domain_id', value)
        if key == 'project_domain_id':
            if self.user_domain_id is None:
                parent.__setattr__('user_domain_id', value)
        if key == 'user_domain_name':
            if self.project_domain_name is None:
                parent.__setattr__('project_domain_name', value)
        if key == 'project_domain_name':
            if self.user_domain_name is None:
                parent.__setattr__('user_domain_name', value)
        # support domain_name coming from config
        if key == 'domain_name':
            parent.__setattr__('user_domain_name', value)
            parent.__setattr__('project_domain_name', value)
        # finally trigger default behaviour for all attributes
        parent.__setattr__(key, value)

    def is_valid(self):
        """
        Valid combinations of v3 credentials (excluding token, scope)
        - User id, password (optional domain)
        - User name, password and its domain id/name
        For the scope, valid combinations are:
        - None
        - Project id (optional domain)
        - Project name and its domain id/name
        """
        valid_user_domain = any(
            [self.user_domain_id is not None,
             self.user_domain_name is not None])
        valid_project_domain = any(
            [self.project_domain_id is not None,
             self.project_domain_name is not None])
        valid_user = any(
            [self.user_id is not None,
             self.username is not None and valid_user_domain])
        valid_project = any(
            [self.project_name is None and self.project_id is None,
             self.project_id is not None,
             self.project_name is not None and valid_project_domain])
        return all([self.password is not None, valid_user, valid_project])
