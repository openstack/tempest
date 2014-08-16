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

from tempest.common import xml_utils as common
from tempest.services.volume.xml import volumes_client


class VolumesV2ClientXML(volumes_client.BaseVolumesClientXML):
    """
    Client class to send CRUD Volume API V2 requests to a Cinder endpoint
    """

    def __init__(self, auth_provider):
        super(VolumesV2ClientXML, self).__init__(auth_provider)

        self.api_version = "v2"
        self.create_resp = 200

    def _parse_volume(self, body):
        vol = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            if tag == 'metadata':
                vol['metadata'] = dict((meta.get('key'),
                                       meta.text) for meta in
                                       child.getchildren())
            else:
                vol[tag] = common.xml_to_json(child)
        self._translate_attributes_to_json(vol)
        return vol

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes."""
        url = 'volumes/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        for v in volumes:
            v = self._check_if_bootable(v)
        return resp, volumes

    def get_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = self._parse_volume(etree.fromstring(body))
        body = self._check_if_bootable(body)
        return resp, body
