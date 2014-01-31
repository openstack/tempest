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

from tempest.common.rest_client import RestClient
from tempest import config

CONF = config.CONF


class ContainerClient(RestClient):
    def __init__(self, username, password, auth_url, tenant_name=None):
        super(ContainerClient, self).__init__(username, password,
                                              auth_url, tenant_name)

        # Overwrites json-specific header encoding in RestClient
        self.headers = {}
        self.service = CONF.object_storage.catalog_type
        self.format = 'json'

    def create_container(self, container_name, metadata=None,
                         metadata_prefix='X-Container-Meta-'):
        """
           Creates a container, with optional metadata passed in as a
           dictionary
        """
        url = str(container_name)
        headers = {}

        if metadata is not None:
            for key in metadata:
                headers[metadata_prefix + key] = metadata[key]

        resp, body = self.put(url, body=None, headers=headers)
        return resp, body

    def delete_container(self, container_name):
        """Deletes the container (if it's empty)."""
        url = str(container_name)
        resp, body = self.delete(url)
        return resp, body

    def update_container_metadata(self, container_name, metadata,
                                  metadata_prefix='X-Container-Meta-'):
        """Updates arbitrary metadata on container."""
        url = str(container_name)
        headers = {}

        if metadata is not None:
            for key in metadata:
                headers[metadata_prefix + key] = metadata[key]

        resp, body = self.post(url, body=None, headers=headers)
        return resp, body

    def delete_container_metadata(self, container_name, metadata,
                                  metadata_prefix='X-Remove-Container-Meta-'):
        """Deletes arbitrary metadata on container."""
        url = str(container_name)
        headers = {}

        if metadata is not None:
            for item in metadata:
                headers[metadata_prefix + item] = 'x'

        resp, body = self.post(url, body=None, headers=headers)
        return resp, body

    def list_container_metadata(self, container_name):
        """
        Retrieves container metadata headers
        """
        url = str(container_name)
        resp, body = self.head(url)
        return resp, body

    def list_all_container_objects(self, container, params=None):
        """
            Returns complete list of all objects in the container, even if
            item count is beyond 10,000 item listing limit.
            Does not require any parameters aside from container name.
        """
        # TODO(dwalleck): Rewrite using json format to avoid newlines at end of
        # obj names. Set limit to API limit - 1 (max returned items = 9999)
        limit = 9999
        if params is not None:
            if 'limit' in params:
                limit = params['limit']

            if 'marker' in params:
                limit = params['marker']

        resp, objlist = self.list_container_contents(container,
                                                     params={'limit': limit})
        return objlist
        """tmp = []
        for obj in objlist:
            tmp.append(obj['name'])
        objlist = tmp

        if len(objlist) >= limit:

            # Increment marker
            marker = objlist[len(objlist) - 1]

            # Get the next chunk of the list
            objlist.extend(_list_all_container_objects(container,
                                                      params={'marker': marker,
                                                              'limit': limit}))
            return objlist
        else:
            # Return final, complete list
            return objlist"""

    def list_container_contents(self, container, params=None):
        """
           List the objects in a container, given the container name

           Returns the container object listing as a plain text list, or as
           xml or json if that option is specified via the 'format' argument.

           Optional Arguments:
           limit = integer
               For an integer value n, limits the number of results to at most
               n values.

           marker = 'string'
               Given a string value x, return object names greater in value
               than the specified marker.

           prefix = 'string'
               For a string value x, causes the results to be limited to names
               beginning with the substring x.

           format = 'json' or 'xml'
               Specify either json or xml to return the respective serialized
               response.
               If json, returns a list of json objects
               if xml, returns a string of xml

           path = 'string'
               For a string value x, return the object names nested in the
               pseudo path (assuming preconditions are met - see below).

           delimiter = 'character'
               For a character c, return all the object names nested in the
               container (without the need for the directory marker objects).
        """

        url = str(container)
        url += '?format=%s' % self.format
        if params:
            url += '&%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body
