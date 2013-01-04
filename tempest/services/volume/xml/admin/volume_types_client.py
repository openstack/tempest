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

import urllib

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11


class VolumeTypesClientXML(RestClientXML):
    """
    Client class to send CRUD Volume Types API requests to a Cinder endpoint
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumeTypesClientXML, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.volume.catalog_type
        self.build_interval = self.config.compute.build_interval
        self.build_timeout = self.config.compute.build_timeout

    def _parse_volume_type(self, body):
        vol_type = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            if tag == 'extra_specs':
                vol_type['extra_specs'] = dict((meta.get('key'),
                                                meta.text)
                                               for meta in list(child))
            else:
                vol_type[tag] = xml_to_json(child)
            return vol_type

    def _parse_volume_type_extra_specs(self, body):
        extra_spec = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            else:
                extra_spec[tag] = xml_to_json(child)
            return extra_spec

    def list_volume_types(self, params=None):
        """List all the volume_types created."""
        url = 'types'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volume_types = []
        if body is not None:
            volume_types += [self._parse_volume_type(vol)
                             for vol in list(body)]
        return resp, volume_types

    def get_volume_type(self, type_id):
        """Returns the details of a single volume_type."""
        url = "types/%s" % str(type_id)
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        return resp, self._parse_volume_type(body)

    def create_volume_type(self, name, **kwargs):
        """
        Creates a new Volume_type.
        name(Required): Name of volume_type.
        Following optional keyword arguments are accepted:
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        vol_type = Element("volume_type", xmlns=XMLNS_11)
        if name:
            vol_type.add_attr('name', name)

        extra_specs = kwargs.get('extra_specs')
        if extra_specs:
            _extra_specs = Element('extra_specs')
            vol_type.append(_extra_specs)
            for key, value in extra_specs.items():
                spec = Element('extra_spec')
                spec.add_attr('key', key)
                spec.append(Text(value))
                _extra_specs.append(spec)

        resp, body = self.post('types', str(Document(vol_type)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume_type(self, type_id):
        """Deletes the Specified Volume_type."""
        return self.delete("types/%s" % str(type_id))

    def list_volume_types_extra_specs(self, vol_type_id, params=None):
        """List all the volume_types extra specs created."""
        url = 'types/%s/extra_specs' % str(vol_type_id)

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        extra_specs = []
        if body is not None:
            extra_specs += [self._parse_volume_type_extra_specs(spec)
                            for spec in list(body)]
        return resp, extra_specs

    def get_volume_type_extra_specs(self, vol_type_id, extra_spec_name):
        """Returns the details of a single volume_type extra spec."""
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        return resp, self._parse_volume_type_extra_specs(body)

    def create_volume_type_extra_specs(self, vol_type_id, extra_spec):
        """
        Creates a new Volume_type extra spec.
        vol_type_id: Id of volume_type.
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        url = "types/%s/extra_specs" % str(vol_type_id)
        extra_specs = Element("extra_specs", xmlns=XMLNS_11)
        if extra_spec:
            for key, value in extra_spec.items():
                spec = Element('extra_spec')
                spec.add_attr('key', key)
                spec.append(Text(value))
                extra_specs.append(spec)

        resp, body = self.post(url, str(Document(extra_specs)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume_type_extra_specs(self, vol_id, extra_spec_name):
        """Deletes the Specified Volume_type extra spec."""
        return self.delete("types/%s/extra_specs/%s" % ((str(vol_id)),
                                                        str(extra_spec_name)))

    def update_volume_type_extra_specs(self, vol_type_id, extra_spec_name,
                                       extra_spec):
        """
        Update a volume_type extra spec.
        vol_type_id: Id of volume_type.
        extra_spec_name: Name of the extra spec to be updated.
        extra_spec: A dictionary of with key as extra_spec_name and the
                    updated value.
        """
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        extra_specs = Element("extra_specs", xmlns=XMLNS_11)
        for key, value in extra_spec.items():
            spec = Element('extra_spec')
            spec.add_attr('key', key)
            spec.append(Text(value))
            extra_specs.append(spec)
        resp, body = self.put(url, str(Document(extra_specs)),
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_volume_type(id)
        except exceptions.NotFound:
            return True
        return False
