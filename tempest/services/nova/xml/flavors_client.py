import urllib

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.nova.xml.common import Document
from tempest.services.nova.xml.common import Element
from tempest.services.nova.xml.common import xml_to_json
from tempest.services.nova.xml.common import XMLNS_11


XMLNS_OS_FLV_EXT_DATA = \
        "http://docs.openstack.org/compute/ext/flavor_extra_data/api/v1.1"


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
        if params != None:
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

    def create_flavor(self, name, ram, vcpus, disk, ephemeral, flavor_id,
                    swap, rxtx):
        """Creates a new flavor or instance type"""
        flavor = Element("flavor",
                         xmlns=XMLNS_11,
                         ram=ram,
                         vcpus=vcpus,
                         disk=disk,
                         id=flavor_id,
                         swap=swap,
                         rxtx_factor=rxtx,
                         name=name)
        flavor.add_attr('xmlns:OS-FLV-EXT-DATA', XMLNS_OS_FLV_EXT_DATA)
        flavor.add_attr('OS-FLV-EXT-DATA:ephemeral', ephemeral)

        resp, body = self.post('flavors', str(Document(flavor)), self.headers)
        body = xml_to_json(etree.fromstring(body))
        flavor = self._format_flavor(body)
        return resp, flavor

    def delete_flavor(self, flavor_id):
        """Deletes the given flavor"""
        return self.delete("flavors/%s" % str(flavor_id), self.headers)
