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
from tempest.common import xml_utils as common
from tempest import config
from tempest import exceptions

CONF = config.CONF


class VolumeTypesClientXML(rest_client.RestClient):
    """
    Client class to send CRUD Volume Types API requests to a Cinder endpoint
    """
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(VolumeTypesClientXML, self).__init__(auth_provider)
        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.compute.build_interval
        self.build_timeout = CONF.compute.build_timeout

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
                vol_type[tag] = common.xml_to_json(child)
            return vol_type

    def _parse_volume_type_extra_specs(self, body):
        extra_spec = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            else:
                extra_spec[tag] = common.xml_to_json(child)
            return extra_spec

    def list_volume_types(self, params=None):
        """List all the volume_types created."""
        url = 'types'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        volume_types = []
        if body is not None:
            volume_types += [self._parse_volume_type(vol)
                             for vol in list(body)]
        self.expected_success(200, resp.status)
        return resp, volume_types

    def get_volume_type(self, type_id):
        """Returns the details of a single volume_type."""
        url = "types/%s" % str(type_id)
        resp, body = self.get(url)
        body = etree.fromstring(body)
        self.expected_success(200, resp.status)
        return resp, self._parse_volume_type(body)

    def create_volume_type(self, name, **kwargs):
        """
        Creates a new Volume_type.
        name(Required): Name of volume_type.
        Following optional keyword arguments are accepted:
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        vol_type = common.Element("volume_type", xmlns=common.XMLNS_11)
        if name:
            vol_type.add_attr('name', name)

        extra_specs = kwargs.get('extra_specs')
        if extra_specs:
            _extra_specs = common.Element('extra_specs')
            vol_type.append(_extra_specs)
            for key, value in extra_specs.items():
                spec = common.Element('extra_spec')
                spec.add_attr('key', key)
                spec.append(common.Text(value))
                _extra_specs.append(spec)

        resp, body = self.post('types', str(common.Document(vol_type)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def delete_volume_type(self, type_id):
        """Deletes the Specified Volume_type."""
        resp, body = self.delete("types/%s" % str(type_id))
        self.expected_success(202, resp.status)

    def list_volume_types_extra_specs(self, vol_type_id, params=None):
        """List all the volume_types extra specs created."""
        url = 'types/%s/extra_specs' % str(vol_type_id)

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        extra_specs = []
        if body is not None:
            extra_specs += [self._parse_volume_type_extra_specs(spec)
                            for spec in list(body)]
        self.expected_success(200, resp.status)
        return resp, extra_specs

    def get_volume_type_extra_specs(self, vol_type_id, extra_spec_name):
        """Returns the details of a single volume_type extra spec."""
        url = "types/%s/extra_specs/%s" % (str(vol_type_id),
                                           str(extra_spec_name))
        resp, body = self.get(url)
        body = etree.fromstring(body)
        self.expected_success(200, resp.status)
        return resp, self._parse_volume_type_extra_specs(body)

    def create_volume_type_extra_specs(self, vol_type_id, extra_spec):
        """
        Creates a new Volume_type extra spec.
        vol_type_id: Id of volume_type.
        extra_specs: A dictionary of values to be used as extra_specs.
        """
        url = "types/%s/extra_specs" % str(vol_type_id)
        extra_specs = common.Element("extra_specs", xmlns=common.XMLNS_11)
        if extra_spec:
            if isinstance(extra_spec, list):
                extra_specs.append(extra_spec)
            else:
                for key, value in extra_spec.items():
                    spec = common.Element('extra_spec')
                    spec.add_attr('key', key)
                    spec.append(common.Text(value))
                    extra_specs.append(spec)
        else:
            extra_specs = None

        resp, body = self.post(url, str(common.Document(extra_specs)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def delete_volume_type_extra_specs(self, vol_id, extra_spec_name):
        """Deletes the Specified Volume_type extra spec."""
        resp, body = self.delete("types/%s/extra_specs/%s" % (
            (str(vol_id)), str(extra_spec_name)))
        self.expected_success(202, resp.status)
        return resp, body

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
        extra_specs = common.Element("extra_specs", xmlns=common.XMLNS_11)

        if extra_spec is not None:
            for key, value in extra_spec.items():
                spec = common.Element('extra_spec')
                spec.add_attr('key', key)
                spec.append(common.Text(value))
                extra_specs.append(spec)

        resp, body = self.put(url, str(common.Document(extra_specs)))
        body = common.xml_to_json(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_volume_type(id)
        except exceptions.NotFound:
            return True
        return False
