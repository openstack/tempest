# Copyright 2014 Hewlett-Packard Development Company, L.P
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

from tempest.common import http
from tempest.common import rest_client
from tempest.common import xml_utils as common
from tempest import config

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v3"


class RegionClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(RegionClientXML, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.region_url = 'adminURL'
        self.api_version = "v3"

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "region":
                array.append(common.xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = common.xml_to_json(body)
        return json

    def request(self, method, url, extra_headers=False, headers=None,
                body=None, wait=None):
        """Overriding the existing HTTP request in super class RestClient."""
        if extra_headers:
            try:
                headers.update(self.get_headers())
            except (ValueError, TypeError):
                headers = self.get_headers()
        dscv = CONF.identity.disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv)
        return super(RegionClientXML, self).request(method, url,
                                                    extra_headers,
                                                    headers=headers,
                                                    body=body)

    def create_region(self, description, **kwargs):
        """Create region."""
        create_region = common.Element("region",
                                       xmlns=XMLNS,
                                       description=description)
        if 'parent_region_id' in kwargs:
            create_region.append(common.Element(
                'parent_region_id', kwargs.get('parent_region_id')))
        if 'unique_region_id' in kwargs:
            resp, body = self.put(
                'regions/%s' % kwargs.get('unique_region_id'),
                str(common.Document(create_region)))
        else:
            resp, body = self.post('regions',
                                   str(common.Document(create_region)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_region(self, region_id, **kwargs):
        """Updates an region with given parameters.
        """
        description = kwargs.get('description', None)
        update_region = common.Element("region",
                                       xmlns=XMLNS,
                                       description=description)
        if 'parent_region_id' in kwargs:
            update_region.append(common.Element('parent_region_id',
                                 kwargs.get('parent_region_id')))

        resp, body = self.patch('regions/%s' % str(region_id),
                                str(common.Document(update_region)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_region(self, region_id):
        """Get Region."""
        url = 'regions/%s' % region_id
        resp, body = self.get(url)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_regions(self, params=None):
        """Get the list of regions."""
        url = 'regions'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def delete_region(self, region_id):
        """Delete region."""
        resp, body = self.delete('regions/%s' % region_id)
        return resp, body
