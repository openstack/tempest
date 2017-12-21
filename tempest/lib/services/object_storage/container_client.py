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

import debtcollector.moves
from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class ContainerClient(rest_client.RestClient):

    def update_container(self, container_name, **headers):
        """Creates or Updates a container

        with optional metadata passed in as a dictionary.
        Full list of allowed headers or value, please refer to the
        official API reference:
        https://developer.openstack.org/api-ref/object-store/#create-container
        """
        url = str(container_name)

        resp, body = self.put(url, body=None, headers=headers)
        self.expected_success([201, 202], resp.status)
        return resp, body

    # NOTE: This alias is for the usability because PUT can be used for both
    # updating/creating a resource and this PUT is mainly used for creating
    # on Swift container API.
    create_container = update_container

    def delete_container(self, container_name):
        """Deletes the container (if it's empty)."""
        url = str(container_name)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return resp, body

    def create_update_or_delete_container_metadata(
            self, container_name,
            create_update_metadata=None,
            delete_metadata=None,
            create_update_metadata_prefix='X-Container-Meta-',
            delete_metadata_prefix='X-Remove-Container-Meta-'):
        """Creates, Updates or deletes an containter metadata entry.

        Container Metadata can be created, updated or deleted based on
        metadata header or value. For detailed info, please refer to the
        official API reference:
        https://developer.openstack.org/api-ref/object-store/#create-update-or-delete-container-metadata
        """
        url = str(container_name)
        headers = {}
        if create_update_metadata:
            for key in create_update_metadata:
                metadata_header_name = create_update_metadata_prefix + key
                headers[metadata_header_name] = create_update_metadata[key]
        if delete_metadata:
            for key in delete_metadata:
                headers[delete_metadata_prefix + key] = delete_metadata[key]

        resp, body = self.post(url, headers=headers, body=None)
        self.expected_success(204, resp.status)
        return resp, body

    update_container_metadata = debtcollector.moves.moved_function(
        create_update_or_delete_container_metadata,
        'update_container_metadata', __name__,
        version='Queens', removal_version='Rocky')

    def list_container_metadata(self, container_name):
        """List all container metadata."""
        url = str(container_name)
        resp, body = self.head(url)
        self.expected_success(204, resp.status)
        return resp, body

    def list_container_objects(self, container_name, params=None):
        """List the objects in a container, given the container name

        Returns the container object listing as a plain text list, or as
        xml or json if that option is specified via the 'format' argument.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/object-store/#show-container-details-and-list-objects
        """

        url = str(container_name)
        if params:
            url += '?'
            url += '&%s' % urllib.urlencode(params)

        resp, body = self.get(url, headers={})
        if params and params.get('format') == 'json':
            body = json.loads(body)
        elif params and params.get('format') == 'xml':
            body = etree.fromstring(body)
        # Else the content-type is plain/text
        else:
            body = [
                obj_name for obj_name in body.decode().split('\n') if obj_name
            ]

        self.expected_success([200, 204], resp.status)
        return resp, body

    list_container_contents = debtcollector.moves.moved_function(
        list_container_objects, 'list_container_contents', __name__,
        version='Queens', removal_version='Rocky')
