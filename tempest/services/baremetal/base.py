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

import functools
import json
import urllib

import six

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


def handle_errors(f):
    """A decorator that allows to ignore certain types of errors."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        param_name = 'ignore_errors'
        ignored_errors = kwargs.get(param_name, tuple())

        if param_name in kwargs:
            del kwargs[param_name]

        try:
            return f(*args, **kwargs)
        except ignored_errors:
            # Silently ignore errors
            pass

    return wrapper


class BaremetalClient(rest_client.RestClient):
    """
    Base Tempest REST client for Ironic API.

    """

    def __init__(self, auth_provider):
        super(BaremetalClient, self).__init__(auth_provider)
        self.service = CONF.baremetal.catalog_type
        self.uri_prefix = ''

    def serialize(self, object_type, object_dict):
        """Serialize an Ironic object."""

        raise NotImplementedError

    def deserialize(self, object_str):
        """Deserialize an Ironic object."""

        raise NotImplementedError

    def _get_uri(self, resource_name, uuid=None, permanent=False):
        """
        Get URI for a specific resource or object.

        :param resource_name: The name of the REST resource, e.g., 'nodes'.
        :param uuid: The unique identifier of an object in UUID format.
        :return: Relative URI for the resource or object.

        """
        prefix = self.uri_prefix if not permanent else ''

        return '{pref}/{res}{uuid}'.format(pref=prefix,
                                           res=resource_name,
                                           uuid='/%s' % uuid if uuid else '')

    def _make_patch(self, allowed_attributes, **kw):
        """
        Create a JSON patch according to RFC 6902.

        :param allowed_attributes: An iterable object that contains a set of
            allowed attributes for an object.
        :param **kw: Attributes and new values for them.
        :return: A JSON path that sets values of the specified attributes to
            the new ones.

        """
        def get_change(kw, path='/'):
            for name, value in six.iteritems(kw):
                if isinstance(value, dict):
                    for ch in get_change(value, path + '%s/' % name):
                        yield ch
                else:
                    yield {'path': path + name,
                           'value': value,
                           'op': 'replace'}

        patch = [ch for ch in get_change(kw)
                 if ch['path'].lstrip('/') in allowed_attributes]

        return patch

    def _list_request(self, resource, permanent=False, **kwargs):
        """
        Get the list of objects of the specified type.

        :param resource: The name of the REST resource, e.g., 'nodes'.
        "param **kw: Parameters for the request.
        :return: A tuple with the server response and deserialized JSON list
                 of objects

        """
        uri = self._get_uri(resource, permanent=permanent)
        if kwargs:
            uri += "?%s" % urllib.urlencode(kwargs)

        resp, body = self.get(uri)

        return resp, self.deserialize(body)

    def _show_request(self, resource, uuid, permanent=False):
        """
        Gets a specific object of the specified type.

        :param uuid: Unique identifier of the object in UUID format.
        :return: Serialized object as a dictionary.

        """
        uri = self._get_uri(resource, uuid=uuid, permanent=permanent)
        resp, body = self.get(uri)

        return resp, self.deserialize(body)

    def _create_request(self, resource, object_type, object_dict):
        """
        Create an object of the specified type.

        :param resource: The name of the REST resource, e.g., 'nodes'.
        :param object_dict: A Python dict that represents an object of the
                            specified type.
        :return: A tuple with the server response and the deserialized created
                 object.

        """
        body = self.serialize(object_type, object_dict)
        uri = self._get_uri(resource)

        resp, body = self.post(uri, body=body)

        return resp, self.deserialize(body)

    def _delete_request(self, resource, uuid):
        """
        Delete specified object.

        :param resource: The name of the REST resource, e.g., 'nodes'.
        :param uuid: The unique identifier of an object in UUID format.
        :return: A tuple with the server response and the response body.

        """
        uri = self._get_uri(resource, uuid)

        resp, body = self.delete(uri)
        return resp, body

    def _patch_request(self, resource, uuid, patch_object):
        """
        Update specified object with JSON-patch.

        :param resource: The name of the REST resource, e.g., 'nodes'.
        :param uuid: The unique identifier of an object in UUID format.
        :return: A tuple with the server response and the serialized patched
                 object.

        """
        uri = self._get_uri(resource, uuid)
        patch_body = json.dumps(patch_object)

        resp, body = self.patch(uri, body=patch_body)
        return resp, self.deserialize(body)

    @handle_errors
    def get_api_description(self):
        """Retrieves all versions of the Ironic API."""

        return self._list_request('', permanent=True)

    @handle_errors
    def get_version_description(self, version='v1'):
        """
        Retrieves the desctription of the API.

        :param version: The version of the API. Default: 'v1'.
        :return: Serialized description of API resources.

        """
        return self._list_request(version, permanent=True)
