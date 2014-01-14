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

from lxml import etree
import urllib

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json


class FloatingIPsClientXML(RestClientXML):
    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FloatingIPsClientXML, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def _parse_floating_ip(self, body):
        json = xml_to_json(body)
        return json

    def list_floating_ips(self, params=None):
        """Returns a list of all floating IPs filtered by any parameters."""
        url = 'os-floating-ips'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_floating_ip_details(self, floating_ip_id):
        """Get the details of a floating IP."""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.get(url, self.headers)
        body = self._parse_floating_ip(etree.fromstring(body))
        if resp.status == 404:
            raise exceptions.NotFound(body)
        return resp, body

    def create_floating_ip(self, pool_name=None):
        """Allocate a floating IP to the project."""
        url = 'os-floating-ips'
        if pool_name:
            doc = Document()
            pool = Element("pool")
            pool.append(Text(pool_name))
            doc.append(pool)
            resp, body = self.post(url, str(doc), self.headers)
        else:
            resp, body = self.post(url, None, self.headers)
        body = self._parse_floating_ip(etree.fromstring(body))
        return resp, body

    def delete_floating_ip(self, floating_ip_id):
        """Deletes the provided floating IP from the project."""
        url = "os-floating-ips/%s" % str(floating_ip_id)
        resp, body = self.delete(url, self.headers)
        return resp, body

    def associate_floating_ip_to_server(self, floating_ip, server_id):
        """Associate the provided floating IP to a specific server."""
        url = "servers/%s/action" % str(server_id)
        doc = Document()
        server = Element("addFloatingIp")
        doc.append(server)
        server.add_attr("address", floating_ip)
        resp, body = self.post(url, str(doc), self.headers)
        return resp, body

    def disassociate_floating_ip_from_server(self, floating_ip, server_id):
        """Disassociate the provided floating IP from a specific server."""
        url = "servers/%s/action" % str(server_id)
        doc = Document()
        server = Element("removeFloatingIp")
        doc.append(server)
        server.add_attr("address", floating_ip)
        resp, body = self.post(url, str(doc), self.headers)
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_floating_ip_details(id)
        except exceptions.NotFound:
            return True
        return False

    def list_floating_ip_pools(self, params=None):
        """Returns a list of all floating IP Pools."""
        url = 'os-floating-ip-pools'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body
