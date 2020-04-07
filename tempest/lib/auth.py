# Copyright 2014 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Rackspace Inc.
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
import re

from oslo_log import log as logging
import six
from six.moves.urllib import parse as urlparse

from tempest.lib import exceptions
from tempest.lib.services.identity.v2 import token_client as json_v2id
from tempest.lib.services.identity.v3 import token_client as json_v3id

ISO8601_FLOAT_SECONDS = '%Y-%m-%dT%H:%M:%S.%fZ'
ISO8601_INT_SECONDS = '%Y-%m-%dT%H:%M:%SZ'
LOG = logging.getLogger(__name__)


def replace_version(url, new_version):
    parts = urlparse.urlparse(url)
    version_path = '/%s' % new_version
    path, subs = re.subn(r'(^|/)+v\d+(?:\.\d+)?',
                         version_path,
                         parts.path,
                         count=1)
    if not subs:
        path = '%s%s' % (parts.path.rstrip('/'), version_path)
    url = urlparse.urlunparse((parts.scheme,
                               parts.netloc,
                               path,
                               parts.params,
                               parts.query,
                               parts.fragment))
    return url


def apply_url_filters(url, filters):
    if filters.get('api_version', None) is not None:
        url = replace_version(url, filters['api_version'])
    parts = urlparse.urlparse(url)
    if filters.get('skip_path', None) is not None and parts.path != '':
        url = urlparse.urlunparse((parts.scheme,
                                   parts.netloc,
                                   '/',
                                   parts.params,
                                   parts.query,
                                   parts.fragment))

    return url


@six.add_metaclass(abc.ABCMeta)
class AuthProvider(object):
    """Provide authentication"""

    SCOPES = set(['project'])

    def __init__(self, credentials, scope='project'):
        """Auth provider __init__

        :param credentials: credentials for authentication
        :param scope: the default scope to be used by the credential providers
                      when requesting a token. Valid values depend on the
                      AuthProvider class implementation, and are defined in
                      the set SCOPES. Default value is 'project'.
        """
        if self.check_credentials(credentials):
            self.credentials = credentials
        else:
            if isinstance(credentials, Credentials):
                password = credentials.get('password')
                message = "Credentials are: " + str(credentials)
                if password is None:
                    message += " Password is not defined."
                else:
                    message += " Password is defined."
                raise exceptions.InvalidCredentials(message)
            else:
                raise TypeError("credentials object is of type %s, which is"
                                " not a valid Credentials object type." %
                                credentials.__class__.__name__)
        self._scope = None
        self.scope = scope
        self.cache = None
        self.alt_auth_data = None
        self.alt_part = None

    def __str__(self):
        return "Creds :{creds}, cached auth data: {cache}".format(
            creds=self.credentials, cache=self.cache)

    @abc.abstractmethod
    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        """Decorate request with authentication data"""
        return

    @abc.abstractmethod
    def _get_auth(self):
        return

    @abc.abstractmethod
    def _fill_credentials(self, auth_data_body):
        return

    def fill_credentials(self):
        """Fill credentials object with data from auth"""
        auth_data = self.get_auth()
        self._fill_credentials(auth_data[1])
        return self.credentials

    @classmethod
    def check_credentials(cls, credentials):
        """Verify credentials are valid."""
        return isinstance(credentials, Credentials) and credentials.is_valid()

    @property
    def auth_data(self):
        """Auth data for set scope"""
        return self.get_auth()

    @property
    def scope(self):
        """Scope used in auth requests"""
        return self._scope

    @auth_data.deleter
    def auth_data(self):
        self.clear_auth()

    def get_auth(self):
        """Returns auth from cache if available, else auth first"""
        if self.cache is None or self.is_expired(self.cache):
            self.set_auth()
        return self.cache

    def set_auth(self):
        """Forces setting auth.

        Forces setting auth, ignores cache if it exists.
        Refills credentials.
        """
        self.cache = self._get_auth()
        self._fill_credentials(self.cache[1])

    def clear_auth(self):
        """Clear access cache

        Can be called to clear the access cache so that next request
        will fetch a new token and base_url.
        """
        self.cache = None
        self.credentials.reset()

    @abc.abstractmethod
    def is_expired(self, auth_data):
        return

    def auth_request(self, method, url, headers=None, body=None, filters=None):
        """Obtains auth data and decorates a request with that.

        :param method: HTTP method of the request
        :param url: relative URL of the request (path)
        :param headers: HTTP headers of the request
        :param body: HTTP body in case of POST / PUT
        :param filters: select a base URL out of the catalog
        :return: a Tuple (url, headers, body)
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
                if auth_req[self.alt_part] == alt_auth_req[self.alt_part]:
                    raise exceptions.BadAltAuth(part=self.alt_part)
                auth_req[self.alt_part] = alt_auth_req[self.alt_part]

            else:
                # If the requested part is not affected by auth, we are
                # not altering auth as expected, raise an exception
                if auth_req[self.alt_part] == orig_req[self.alt_part]:
                    raise exceptions.BadAltAuth(part=self.alt_part)
                # If alt auth data is None, skip auth in the requested part
                auth_req[self.alt_part] = orig_req[self.alt_part]

            # Next auth request will be normal, unless otherwise requested
            self.reset_alt_auth_data()

        return auth_req['url'], auth_req['headers'], auth_req['body']

    def reset_alt_auth_data(self):
        """Configure auth provider to provide valid authentication data"""
        self.alt_part = None
        self.alt_auth_data = None

    def set_alt_auth_data(self, request_part, auth_data):
        """Alternate auth data on next request

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
        """Extracts the base_url based on provided filters"""
        return

    @scope.setter
    def scope(self, value):
        """Set the scope to be used in token requests

        :param scope: scope to be used. If the scope is different, clear caches
        """
        if value not in self.SCOPES:
            raise exceptions.InvalidScope(
                scope=value, auth_provider=self.__class__.__name__)
        if value != self.scope:
            self.clear_auth()
            self._scope = value


class KeystoneAuthProvider(AuthProvider):

    EXPIRY_DATE_FORMATS = (ISO8601_FLOAT_SECONDS, ISO8601_INT_SECONDS)

    token_expiry_threshold = datetime.timedelta(seconds=60)

    def __init__(self, credentials, auth_url,
                 disable_ssl_certificate_validation=None,
                 ca_certs=None, trace_requests=None, scope='project',
                 http_timeout=None, proxy_url=None):
        super(KeystoneAuthProvider, self).__init__(credentials, scope)
        self.dscv = disable_ssl_certificate_validation
        self.ca_certs = ca_certs
        self.trace_requests = trace_requests
        self.http_timeout = http_timeout
        self.proxy_url = proxy_url
        self.auth_url = auth_url
        self.auth_client = self._auth_client(auth_url)

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        if auth_data is None:
            auth_data = self.get_auth()
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
        """Auth parameters to be passed to the token request

        By default all fields available in Credentials are passed to the
        token request. Scope may affect this.
        """
        return

    def _get_auth(self):
        # Bypasses the cache
        auth_func = getattr(self.auth_client, 'get_token')
        auth_params = self._auth_params()

        # returns token, auth_data
        token, auth_data = auth_func(**auth_params)
        return token, auth_data

    def _parse_expiry_time(self, expiry_string):
        expiry = None
        for date_format in self.EXPIRY_DATE_FORMATS:
            try:
                expiry = datetime.datetime.strptime(
                    expiry_string, date_format)
            except ValueError:
                pass
        if expiry is None:
            raise ValueError(
                "time data '{data}' does not match any of the "
                "expected formats: {formats}".format(
                    data=expiry_string, formats=self.EXPIRY_DATE_FORMATS))
        return expiry

    def get_token(self):
        return self.get_auth()[0]


class KeystoneV2AuthProvider(KeystoneAuthProvider):
    """Provides authentication based on the Identity V2 API

    The Keystone Identity V2 API defines both unscoped and project scoped
    tokens. This auth provider only implements 'project'.
    """

    SCOPES = set(['project'])

    def _auth_client(self, auth_url):
        return json_v2id.TokenClient(
            auth_url, disable_ssl_certificate_validation=self.dscv,
            ca_certs=self.ca_certs, trace_requests=self.trace_requests,
            http_timeout=self.http_timeout, proxy_url=self.proxy_url)

    def _auth_params(self):
        """Auth parameters to be passed to the token request

        All fields available in Credentials are passed to the token request.
        """
        return dict(
            user=self.credentials.username,
            password=self.credentials.password,
            tenant=self.credentials.tenant_name,
            auth_data=True)

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
        """Base URL from catalog

        :param filters: Used to filter results

        Filters can be:

        - service: service type name such as compute, image, etc.
        - region: service region name
        - name: service name, only if service exists
        - endpoint_type: type of endpoint such as
            adminURL, publicURL, internalURL
        - api_version: the version of api used to replace catalog version
        - skip_path: skips the suffix path of the url and uses base URL

        :rtype: string
        :return: url with filters applied
        """
        if auth_data is None:
            auth_data = self.get_auth()
        token, _auth_data = auth_data
        service = filters.get('service')
        region = filters.get('region')
        name = filters.get('name')
        endpoint_type = filters.get('endpoint_type', 'publicURL')

        if service is None:
            raise exceptions.EndpointNotFound("No service provided")

        _base_url = None
        for ep in _auth_data['serviceCatalog']:
            if ep["type"] == service:
                if name is not None and ep["name"] != name:
                    continue
                for _ep in ep['endpoints']:
                    if region is not None and _ep['region'] == region:
                        _base_url = _ep.get(endpoint_type)
                if not _base_url:
                    # No region or name matching, use the first
                    _base_url = ep['endpoints'][0].get(endpoint_type)
                break
        if _base_url is None:
            raise exceptions.EndpointNotFound(
                "service: %s, region: %s, endpoint_type: %s, name: %s" %
                (service, region, endpoint_type, name))
        return apply_url_filters(_base_url, filters)

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = self._parse_expiry_time(access['token']['expires'])
        return (expiry - self.token_expiry_threshold <=
                datetime.datetime.utcnow())


class KeystoneV3AuthProvider(KeystoneAuthProvider):
    """Provides authentication based on the Identity V3 API"""

    SCOPES = set(['project', 'domain', 'unscoped', None])

    def _auth_client(self, auth_url):
        return json_v3id.V3TokenClient(
            auth_url, disable_ssl_certificate_validation=self.dscv,
            ca_certs=self.ca_certs, trace_requests=self.trace_requests,
            http_timeout=self.http_timeout, proxy_url=self.proxy_url)

    def _auth_params(self):
        """Auth parameters to be passed to the token request

        Fields available in Credentials are passed to the token request,
        depending on the value of scope. Valid values for scope are: "project",
        "domain". Any other string (e.g. "unscoped") or None will lead to an
        unscoped token request.
        """

        auth_params = dict(
            user_id=self.credentials.user_id,
            username=self.credentials.username,
            user_domain_id=self.credentials.user_domain_id,
            user_domain_name=self.credentials.user_domain_name,
            password=self.credentials.password,
            auth_data=True)

        if self.scope == 'project':
            auth_params.update(
                project_domain_id=self.credentials.project_domain_id,
                project_domain_name=self.credentials.project_domain_name,
                project_id=self.credentials.project_id,
                project_name=self.credentials.project_name)

        if self.scope == 'domain':
            auth_params.update(
                domain_id=self.credentials.domain_id,
                domain_name=self.credentials.domain_name)

        return auth_params

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
                self.credentials.project_domain_name = (
                    project['domain']['name'])
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
        """Base URL from catalog

        If scope is not 'project', it may be that there is not catalog in
        the auth_data. In such case, as long as the requested service is
        'identity', we can use the original auth URL to build the base_url.

        :param filters: Used to filter results

        Filters can be:

        - service: service type name such as compute, image, etc.
        - region: service region name
        - name: service name, only if service exists
        - endpoint_type: type of endpoint such as
            adminURL, publicURL, internalURL
        - api_version: the version of api used to replace catalog version
        - skip_path: skips the suffix path of the url and uses base URL

        :rtype: string
        :return: url with filters applied
        """
        if auth_data is None:
            auth_data = self.get_auth()
        token, _auth_data = auth_data
        service = filters.get('service')
        region = filters.get('region')
        name = filters.get('name')
        endpoint_type = filters.get('endpoint_type', 'public')

        if service is None:
            raise exceptions.EndpointNotFound("No service provided")

        if 'URL' in endpoint_type:
            endpoint_type = endpoint_type.replace('URL', '')
        _base_url = None
        catalog = _auth_data.get('catalog', [])

        # Select entries with matching service type
        service_catalog = [ep for ep in catalog if ep['type'] == service]
        if service_catalog:
            if name is not None:
                service_catalog = (
                    [ep for ep in service_catalog if ep['name'] == name])
                if service_catalog:
                    service_catalog = service_catalog[0]['endpoints']
                else:
                    raise exceptions.EndpointNotFound(name)
            else:
                service_catalog = service_catalog[0]['endpoints']
        else:
            if not catalog and service == 'identity':
                # NOTE(andreaf) If there's no catalog at all and the service
                # is identity, it's a valid use case. Having a non-empty
                # catalog with no identity in it is not valid instead.
                msg = ('Got an empty catalog. Scope: %s. '
                       'Falling back to configured URL for %s: %s')
                LOG.debug(msg, self.scope, service, self.auth_url)
                return apply_url_filters(self.auth_url, filters)
            else:
                # No matching service
                msg = ('No matching service found in the catalog.\n'
                       'Scope: %s, Credentials: %s\n'
                       'Auth data: %s\n'
                       'Service: %s, Region: %s, endpoint_type: %s\n'
                       'Catalog: %s')
                raise exceptions.EndpointNotFound(msg % (
                    self.scope, self.credentials, _auth_data, service, region,
                    endpoint_type, catalog))
        # Filter by endpoint type (interface)
        filtered_catalog = [ep for ep in service_catalog if
                            ep['interface'] == endpoint_type]
        if not filtered_catalog:
            # No matching type, keep all and try matching by region at least
            filtered_catalog = service_catalog
        # Filter by region
        filtered_catalog = [ep for ep in filtered_catalog if
                            ep['region'] == region]
        if not filtered_catalog:
            # No matching region (or name), take the first endpoint
            filtered_catalog = [service_catalog[0]]
        # There should be only one match. If not take the first.
        _base_url = filtered_catalog[0].get('url', None)
        if _base_url is None:
            raise exceptions.EndpointNotFound(service)
        return apply_url_filters(_base_url, filters)

    def is_expired(self, auth_data):
        _, access = auth_data
        expiry = self._parse_expiry_time(access['expires_at'])
        return (expiry - self.token_expiry_threshold <=
                datetime.datetime.utcnow())


def is_identity_version_supported(identity_version):
    return identity_version in IDENTITY_VERSION


def get_credentials(auth_url, fill_in=True, identity_version='v2',
                    disable_ssl_certificate_validation=None, ca_certs=None,
                    trace_requests=None, http_timeout=None, proxy_url=None,
                    **kwargs):
    """Builds a credentials object based on the configured auth_version

    :param auth_url (string): Full URI of the OpenStack Identity API(Keystone)
           which is used to fetch the token from Identity service.
    :param fill_in (boolean): obtain a token and fill in all credential
           details provided by the identity service. When fill_in is not
           specified, credentials are not validated. Validation can be invoked
           by invoking ``is_valid()``
    :param identity_version (string): identity API version is used to
           select the matching auth provider and credentials class
    :param disable_ssl_certificate_validation: whether to enforce SSL
           certificate validation in SSL API requests to the auth system
    :param ca_certs: CA certificate bundle for validation of certificates
           in SSL API requests to the auth system
    :param trace_requests: trace in log API requests to the auth system
    :param http_timeout: timeout in seconds to wait for the http request to
           return
    :param proxy_url: URL of HTTP(s) proxy used when fill_in is True
    :param kwargs (dict): Dict of credential key/value pairs

    Examples:

        Returns credentials from the provided parameters:
        >>> get_credentials(username='foo', password='bar')

        Returns credentials including IDs:
        >>> get_credentials(username='foo', password='bar', fill_in=True)
    """
    if not is_identity_version_supported(identity_version):
        raise exceptions.InvalidIdentityVersion(
            identity_version=identity_version)

    credential_class, auth_provider_class = IDENTITY_VERSION.get(
        identity_version)

    creds = credential_class(**kwargs)
    # Fill in the credentials fields that were not specified
    if fill_in:
        dscv = disable_ssl_certificate_validation
        auth_provider = auth_provider_class(
            creds, auth_url, disable_ssl_certificate_validation=dscv,
            ca_certs=ca_certs, trace_requests=trace_requests,
            http_timeout=http_timeout, proxy_url=proxy_url)
        creds = auth_provider.fill_credentials()
    return creds


class Credentials(object):
    """Set of credentials for accessing OpenStack services

    ATTRIBUTES: list of valid class attributes representing credentials.
    """

    ATTRIBUTES = []
    COLLISIONS = []

    def __init__(self, **kwargs):
        """Enforce the available attributes at init time (only).

        Additional attributes can still be set afterwards if tests need
        to do so.
        """
        self._initial = kwargs
        self._apply_credentials(kwargs)

    def _apply_credentials(self, attr):
        for (key1, key2) in self.COLLISIONS:
            val1 = attr.get(key1)
            val2 = attr.get(key2)
            if val1 and val2 and val1 != val2:
                msg = ('Cannot have conflicting values for %s and %s' %
                       (key1, key2))
                raise exceptions.InvalidCredentials(msg)
        for key in attr:
            if key in self.ATTRIBUTES:
                setattr(self, key, attr[key])
            else:
                msg = '%s is not a valid attr for %s' % (key, self.__class__)
                raise exceptions.InvalidCredentials(msg)

    def __str__(self):
        """Represent only attributes included in self.ATTRIBUTES"""
        attrs = [attr for attr in self.ATTRIBUTES if attr != 'password']
        _repr = dict((k, getattr(self, k)) for k in attrs)
        return str(_repr)

    def __eq__(self, other):
        """Credentials are equal if attributes in self.ATTRIBUTES are equal"""
        return str(self) == str(other)

    def __ne__(self, other):
        """Contrary to the __eq__"""
        return not self.__eq__(other)

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

    def get(self, item, default=None):
        # In this patch act as dict for backward compatibility
        try:
            return getattr(self, item)
        except AttributeError:
            return default

    def get_init_attributes(self):
        return self._initial.keys()

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

    ATTRIBUTES = ['username', 'password', 'tenant_name', 'user_id',
                  'tenant_id', 'project_id', 'project_name']
    COLLISIONS = [('project_name', 'tenant_name'), ('project_id', 'tenant_id')]

    def __str__(self):
        """Represent only attributes included in self.ATTRIBUTES"""
        attrs = [attr for attr in self.ATTRIBUTES if attr != 'password']
        _repr = dict((k, getattr(self, k)) for k in attrs)
        return str(_repr)

    def __setattr__(self, key, value):
        # NOTE(andreaf) In order to ease the migration towards 'project' we
        # support v2 credentials configured with 'project' and translate it
        # to tenant on the fly. The original kwargs are stored for clients
        # that may rely on them. We also set project when tenant is defined
        # so clients can rely on project being part of credentials.
        parent = super(KeystoneV2Credentials, self)
        # for project_* set tenant only
        if key == 'project_id':
            parent.__setattr__('tenant_id', value)
        elif key == 'project_name':
            parent.__setattr__('tenant_name', value)
        if key == 'tenant_id':
            parent.__setattr__('project_id', value)
        elif key == 'tenant_name':
            parent.__setattr__('project_name', value)
        # trigger default behaviour for all attributes
        parent.__setattr__(key, value)

    def is_valid(self):
        """Check of credentials (no API call)

        Minimum set of valid credentials, are username and password.
        Tenant is optional.
        """
        return None not in (self.username, self.password)


class KeystoneV3Credentials(Credentials):
    """Credentials suitable for the Keystone Identity V3 API"""

    ATTRIBUTES = ['domain_id', 'domain_name', 'password', 'username',
                  'project_domain_id', 'project_domain_name', 'project_id',
                  'project_name', 'tenant_id', 'tenant_name', 'user_domain_id',
                  'user_domain_name', 'user_id']
    COLLISIONS = [('project_name', 'tenant_name'), ('project_id', 'tenant_id')]

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
            if self.user_domain_name is None:
                parent.__setattr__('user_domain_name', value)
            if self.project_domain_name is None:
                parent.__setattr__('project_domain_name', value)
        # finally trigger default behaviour for all attributes
        parent.__setattr__(key, value)

    def is_valid(self):
        """Check of credentials (no API call)

        Valid combinations of v3 credentials (excluding token)
        - User id, password (optional domain)
        - User name, password and its domain id/name
        For the scope, valid combinations are:
        - None
        - Project id (optional domain)
        - Project name and its domain id/name
        - Domain id
        - Domain name
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
        valid_project_scope = any(
            [self.project_name is None and self.project_id is None,
             self.project_id is not None,
             self.project_name is not None and valid_project_domain])
        valid_domain_scope = any(
            [self.domain_id is None and self.domain_name is None,
             self.domain_id or self.domain_name])
        return all([self.password is not None,
                    valid_user,
                    valid_project_scope and valid_domain_scope])


IDENTITY_VERSION = {'v2': (KeystoneV2Credentials, KeystoneV2AuthProvider),
                    'v3': (KeystoneV3Credentials, KeystoneV3AuthProvider)}
