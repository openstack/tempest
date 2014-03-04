# Copyright 2012 IBM Corp.
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

import urllib

from lxml import etree

from tempest.common import rest_client
from tempest.common import waiters
from tempest.common import xml_utils
from tempest import config
from tempest import exceptions

CONF = config.CONF


class ImagesClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(ImagesClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type
        self.build_interval = CONF.compute.build_interval
        self.build_timeout = CONF.compute.build_timeout

    def _parse_server(self, node):
        data = xml_utils.xml_to_json(node)
        return self._parse_links(node, data)

    def _parse_image(self, node):
        """Parses detailed XML image information into dictionary."""
        data = xml_utils.xml_to_json(node)

        self._parse_links(node, data)

        # parse all metadata
        if 'metadata' in data:
            tag = node.find('{%s}metadata' % xml_utils.XMLNS_11)
            data['metadata'] = dict((x.get('key'), x.text)
                                    for x in tag.getchildren())

        # parse server information
        if 'server' in data:
            tag = node.find('{%s}server' % xml_utils.XMLNS_11)
            data['server'] = self._parse_server(tag)
        return data

    def _parse_links(self, node, data):
        """Append multiple links under a list."""
        # look for links
        if 'link' in data:
            # remove single link element
            del data['link']
            data['links'] = [xml_utils.xml_to_json(x) for x in
                             node.findall('{http://www.w3.org/2005/Atom}link')]
        return data

    def _parse_images(self, xml):
        data = {'images': []}
        images = xml.getchildren()
        for image in images:
            data['images'].append(self._parse_image(image))
        return data

    def _parse_key_value(self, node):
        """Parse <foo key='key'>value</foo> data into {'key': 'value'}."""
        data = {}
        for node in node.getchildren():
            data[node.get('key')] = node.text
        return data

    def _parse_metadata(self, node):
        """Parse the response body without children."""
        data = {}
        data[node.get('key')] = node.text
        return data

    def create_image(self, server_id, name, meta=None):
        """Creates an image of the original server."""
        post_body = xml_utils.Element('createImage', name=name)

        if meta:
            metadata = xml_utils.Element('metadata')
            post_body.append(metadata)
            for k, v in meta.items():
                data = xml_utils.Element('meta', key=k)
                data.append(xml_utils.Text(v))
                metadata.append(data)
        resp, body = self.post('servers/%s/action' % str(server_id),
                               str(xml_utils.Document(post_body)))
        return resp, body

    def list_images(self, params=None):
        """Returns a list of all images filtered by any parameters."""
        url = 'images'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = self._parse_images(etree.fromstring(body))
        return resp, body['images']

    def list_images_with_detail(self, params=None):
        """Returns a detailed list of images filtered by any parameters."""
        url = 'images/detail'
        if params:
            param_list = urllib.urlencode(params)

            url = "images/detail?" + param_list

        resp, body = self.get(url)
        body = self._parse_images(etree.fromstring(body))
        return resp, body['images']

    def get_image(self, image_id):
        """Returns the details of a single image."""
        resp, body = self.get("images/%s" % str(image_id))
        self.expected_success(200, resp)
        body = self._parse_image(etree.fromstring(body))
        return resp, body

    def delete_image(self, image_id):
        """Deletes the provided image."""
        return self.delete("images/%s" % str(image_id))

    def wait_for_image_status(self, image_id, status):
        """Waits for an image to reach a given status."""
        waiters.wait_for_image_status(self, image_id, status)

    def _metadata_body(self, meta):
        post_body = xml_utils.Element('metadata')
        for k, v in meta.items():
            data = xml_utils.Element('meta', key=k)
            data.append(xml_utils.Text(v))
            post_body.append(data)
        return post_body

    def list_image_metadata(self, image_id):
        """Lists all metadata items for an image."""
        resp, body = self.get("images/%s/metadata" % str(image_id))
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def set_image_metadata(self, image_id, meta):
        """Sets the metadata for an image."""
        post_body = self._metadata_body(meta)
        resp, body = self.put('images/%s/metadata' % image_id,
                              str(xml_utils.Document(post_body)))
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def update_image_metadata(self, image_id, meta):
        """Updates the metadata for an image."""
        post_body = self._metadata_body(meta)
        resp, body = self.post('images/%s/metadata' % str(image_id),
                               str(xml_utils.Document(post_body)))
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def get_image_metadata_item(self, image_id, key):
        """Returns the value for a specific image metadata key."""
        resp, body = self.get("images/%s/metadata/%s.xml" %
                              (str(image_id), key))
        body = self._parse_metadata(etree.fromstring(body))
        return resp, body

    def set_image_metadata_item(self, image_id, key, meta):
        """Sets the value for a specific image metadata key."""
        for k, v in meta.items():
            post_body = xml_utils.Element('meta', key=key)
            post_body.append(xml_utils.Text(v))
        resp, body = self.put('images/%s/metadata/%s' % (str(image_id), key),
                              str(xml_utils.Document(post_body)))
        body = xml_utils.xml_to_json(etree.fromstring(body))
        return resp, body

    def update_image_metadata_item(self, image_id, key, meta):
        """Sets the value for a specific image metadata key."""
        post_body = xml_utils.Document('meta', xml_utils.Text(meta), key=key)
        resp, body = self.put('images/%s/metadata/%s' % (str(image_id), key),
                              post_body)
        body = xml_utils.xml_to_json(etree.fromstring(body))
        return resp, body['meta']

    def delete_image_metadata_item(self, image_id, key):
        """Deletes a single image metadata key/value pair."""
        return self.delete("images/%s/metadata/%s" % (str(image_id), key))

    def is_resource_deleted(self, id):
        try:
            self.get_image(id)
        except exceptions.NotFound:
            return True
        return False
