# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM
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

import time
import urllib

from lxml import etree

from tempest import exceptions
from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11


class ImagesClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ImagesClientXML, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.compute.catalog_type
        self.build_interval = self.config.compute.build_interval
        self.build_timeout = self.config.compute.build_timeout

    def _parse_server(self, node):
        json = xml_to_json(node)
        return self._parse_links(node, json)

    def _parse_image(self, node):
        """Parses detailed XML image information into dictionary"""
        json = xml_to_json(node)

        self._parse_links(node, json)

        # parse all metadata
        if 'metadata' in json:
            tag = node.find('{%s}metadata' % XMLNS_11)
            json['metadata'] = dict((x.get('key'), x.text)
                                    for x in tag.getchildren())

        # parse server information
        if 'server' in json:
            tag = node.find('{%s}server' % XMLNS_11)
            json['server'] = self._parse_server(tag)
        return json

    def _parse_links(self, node, json):
        """Append multiple links under a list"""
        # look for links
        if 'link' in json:
            # remove single link element
            del json['link']
            json['links'] = [xml_to_json(x) for x in
                             node.findall('{http://www.w3.org/2005/Atom}link')]
        return json

    def create_image(self, server_id, name, meta=None):
        """Creates an image of the original server"""
        post_body = Element('createImage', name=name)

        if meta:
            metadata = Element('metadata')
            post_body.append(metadata)
            for k, v in meta.items():
                data = Element('meta', key=k)
                data.append(Text(v))
                metadata.append(data)
        resp, body = self.post('servers/%s/action' % str(server_id),
                               str(Document(post_body)), self.headers)
        return resp, body

    def list_images(self, params=None):
        """Returns a list of all images filtered by any parameters"""
        url = 'images'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['images']

    def list_images_with_detail(self, params=None):
        """Returns a detailed list of images filtered by any parameters"""
        url = 'images/detail'
        if params:
            param_list = urllib.urlencode(params)

            url = "images/detail?" + param_list

        resp, body = self.get(url, self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['images']

    def get_image(self, image_id):
        """Returns the details of a single image"""
        resp, body = self.get("images/%s" % str(image_id), self.headers)
        body = self._parse_image(etree.fromstring(body))
        return resp, body

    def delete_image(self, image_id):
        """Deletes the provided image"""
        return self.delete("images/%s" % str(image_id), self.headers)

    def wait_for_image_resp_code(self, image_id, code):
        """
        Waits until the HTTP response code for the request matches the
        expected value
        """
        resp, body = self.get("images/%s" % str(image_id), self.headers)
        start = int(time.time())

        while resp.status != code:
            time.sleep(self.build_interval)
            resp, body = self.get("images/%s" % str(image_id), self.headers)

            if int(time.time()) - start >= self.build_timeout:
                raise exceptions.TimeoutException

    def wait_for_image_status(self, image_id, status):
        """Waits for an image to reach a given status."""
        resp, image = self.get_image(image_id)
        start = int(time.time())

        while image['status'] != status:
            time.sleep(self.build_interval)
            resp, image = self.get_image(image_id)
            if image['status'] == 'ERROR':
                raise exceptions.AddImageException(image_id=image_id)

            if int(time.time()) - start >= self.build_timeout:
                raise exceptions.TimeoutException

    def list_image_metadata(self, image_id):
        """Lists all metadata items for an image"""
        resp, body = self.get("images/%s/metadata" % str(image_id),
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['metadata']

    def set_image_metadata(self, image_id, meta):
        """Sets the metadata for an image"""
        post_body = json.dumps({'metadata': meta})
        resp, body = self.put('images/%s/metadata' % str(image_id),
                              post_body, self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['metadata']

    def update_image_metadata(self, image_id, meta):
        """Updates the metadata for an image"""
        post_body = Element('metadata', meta)
        for k, v in meta:
            metadata = Element('meta', key=k)
            text = Text(v)
            metadata.append(text)
            post_body.append(metadata)

        resp, body = self.post('images/%s/metadata' % str(image_id),
                               post_body, self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['metadata']

    def get_image_metadata_item(self, image_id, key):
        """Returns the value for a specific image metadata key"""
        resp, body = self.get("images/%s/metadata/%s.xml" %
                              (str(image_id), key), self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['meta']

    def set_image_metadata_item(self, image_id, key, meta):
        """Sets the value for a specific image metadata key"""
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('images/%s/metadata/%s' % (str(image_id), key),
                              post_body, self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body['meta']

    def delete_image_metadata_item(self, image_id, key):
        """Deletes a single image metadata key/value pair"""
        resp, body = self.delete("images/%s/metadata/%s" % (str(image_id), key,
                                 self.headers))
        return resp, body
