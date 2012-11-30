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

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import Document


class VolumesClientXML(RestClientXML):
    """
    Client class to send CRUD Volume API requests to a Cinder endpoint
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumesClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type
        self.build_interval = self.config.compute.build_interval
        self.build_timeout = self.config.compute.build_timeout

    def _parse_volume(self, body):
        vol = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            if tag == 'metadata':
                vol['metadata'] = dict((meta.get('key'),
                                        meta.text) for meta in list(child))
            else:
                vol[tag] = xml_to_json(child)
            return vol

    def list_volumes(self, params=None):
        """List all the volumes created"""
        url = 'volumes'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        return resp, volumes

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes"""
        url = 'volumes/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        return resp, volumes

    def get_volume(self, volume_id, wait=None):
        """Returns the details of a single volume"""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url, self.headers, wait=wait)
        body = etree.fromstring(body)
        return resp, self._parse_volume(body)

    def create_volume(self, size, display_name=None, metadata=None):
        """Creates a new Volume.

        :param size: Size of volume in GB. (Required)
        :param display_name: Optional Volume Name.
        :param metadata: An optional dictionary of values for metadata.
        """
        volume = Element("volume", xmlns=XMLNS_11, size=size)
        if display_name:
            volume.add_attr('display_name', display_name)

        if metadata:
            _metadata = Element('metadata')
            volume.append(_metadata)
            for key, value in metadata.items():
                meta = Element('meta')
                meta.add_attr('key', key)
                meta.append(Text(value))
                _metadata.append(meta)

        resp, body = self.post('volumes', str(Document(volume)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume"""
        return self.delete("volumes/%s" % str(volume_id))

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status"""
        resp, body = self.get_volume(volume_id)
        volume_name = body['displayName']
        volume_status = body['status']
        start = int(time.time())

        while volume_status != status:
            time.sleep(self.build_interval)
            resp, body = self.get_volume(volume_id)
            volume_status = body['status']
            if volume_status == 'error':
                raise exceptions.VolumeBuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = 'Volume %s failed to reach %s status within '\
                          'the required time (%s s).' % (volume_name, status,
                                                         self.build_timeout)
                raise exceptions.TimeoutException(message)

    def is_resource_deleted(self, id):
        try:
            self.get_volume(id, wait=True)
        except exceptions.NotFound:
            return True
        return False
