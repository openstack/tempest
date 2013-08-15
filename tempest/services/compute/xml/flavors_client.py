# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11


XMLNS_OS_FLV_EXT_DATA = \
    "http://docs.openstack.org/compute/ext/flavor_extra_data/api/v1.1"
XMLNS_OS_FLV_ACCESS = \
    "http://docs.openstack.org/compute/ext/flavor_access/api/v1.1"
XMLNS_OS_FLV_WITH_EXT_SPECS = \
    "http://docs.openstack.org/compute/ext/flavor_with_extra_specs/api/v2.0"


class FlavorsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FlavorsClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _format_flavor(self, f):
        flavor = {'links': []}
        for k, v in f.items():
            if k == 'link':
                flavor['links'].append(v)
                continue

            if k == '{%s}ephemeral' % XMLNS_OS_FLV_EXT_DATA:
                k = 'OS-FLV-EXT-DATA:ephemeral'

            if k == '{%s}extra_specs' % XMLNS_OS_FLV_WITH_EXT_SPECS:
                k = 'OS-FLV-WITH-EXT-SPECS:extra_specs'
                flavor[k] = dict(v)
                continue

            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass

            flavor[k] = v

        return flavor

    def _parse_array(self, node):
        return [self._format_flavor(xml_to_json(x)) for x in node]

    def _list_flavors(self, url, params):
        if params:
            url += "?%s" % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        flavors = self._parse_array(etree.fromstring(body))
        return resp, flavors

    def list_flavors(self, params=None):
        url = 'flavors'
        return self._list_flavors(url, params)

    def list_flavors_with_detail(self, params=None):
        url = 'flavors/detail'
        return self._list_flavors(url, params)

    def get_flavor_details(self, flavor_id):
        resp, body = self.get("flavors/%s" % str(flavor_id), self.headers)
        body = xml_to_json(etree.fromstring(body))
        flavor = self._format_flavor(body)
        return resp, flavor

    def create_flavor(self, name, ram, vcpus, disk, flavor_id, **kwargs):
        """Creates a new flavor or instance type."""
        flavor = Element("flavor",
                         xmlns=XMLNS_11,
                         ram=ram,
                         vcpus=vcpus,
                         disk=disk,
                         id=flavor_id,
                         name=name)
        if kwargs.get('rxtx'):
            flavor.add_attr('rxtx_factor', kwargs.get('rxtx'))
        if kwargs.get('swap'):
            flavor.add_attr('swap', kwargs.get('swap'))
        if kwargs.get('ephemeral'):
            flavor.add_attr('OS-FLV-EXT-DATA:ephemeral',
                            kwargs.get('ephemeral'))
        if kwargs.get('is_public'):
            flavor.add_attr('os-flavor-access:is_public',
                            kwargs.get('is_public'))
        flavor.add_attr('xmlns:OS-FLV-EXT-DATA', XMLNS_OS_FLV_EXT_DATA)
        flavor.add_attr('xmlns:os-flavor-access', XMLNS_OS_FLV_ACCESS)
        resp, body = self.post('flavors', str(Document(flavor)), self.headers)
        body = xml_to_json(etree.fromstring(body))
        flavor = self._format_flavor(body)
        return resp, flavor

    def delete_flavor(self, flavor_id):
        """Deletes the given flavor."""
        return self.delete("flavors/%s" % str(flavor_id), self.headers)

    def is_resource_deleted(self, id):
        # Did not use get_flavor_details(id) for verification as it gives
        # 200 ok even for deleted id. LP #981263
        # we can remove the loop here and use get by ID when bug gets sortedout
        resp, flavors = self.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['id'] == id:
                return False
        return True

    def set_flavor_extra_spec(self, flavor_id, specs):
        """Sets extra Specs to the mentioned flavor."""
        extra_specs = Element("extra_specs")
        for key in specs.keys():
            extra_specs.add_attr(key, specs[key])
        resp, body = self.post('flavors/%s/os-extra_specs' % flavor_id,
                               str(Document(extra_specs)), self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def get_flavor_extra_spec(self, flavor_id):
        """Gets extra Specs of the mentioned flavor."""
        resp, body = self.get('flavors/%s/os-extra_specs' % flavor_id,
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def unset_flavor_extra_spec(self, flavor_id, key):
        """Unsets an extra spec based on the mentioned flavor and key."""
        return self.delete('flavors/%s/os-extra_specs/%s' % (str(flavor_id),
                           key))

    def _parse_array_access(self, node):
        return [xml_to_json(x) for x in node]

    def add_flavor_access(self, flavor_id, tenant_id):
        """Add flavor access for the specified tenant."""
        doc = Document()
        server = Element("addTenantAccess")
        doc.append(server)
        server.add_attr("tenant", tenant_id)
        resp, body = self.post('flavors/%s/action' % str(flavor_id),
                               str(doc), self.headers)
        body = self._parse_array_access(etree.fromstring(body))
        return resp, body

    def remove_flavor_access(self, flavor_id, tenant_id):
        """Remove flavor access from the specified tenant."""
        doc = Document()
        server = Element("removeTenantAccess")
        doc.append(server)
        server.add_attr("tenant", tenant_id)
        resp, body = self.post('flavors/%s/action' % str(flavor_id),
                               str(doc), self.headers)
        body = self._parse_array_access(etree.fromstring(body))
        return resp, body
