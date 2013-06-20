# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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
from tempest.services.compute.xml.common import XMLNS_11


class SecurityGroupsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(SecurityGroupsClientXML, self).__init__(
            config, username, password,
            auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_to_json(body)
        return json

    def list_security_groups(self, params=None):
        """List all security groups for a user."""

        url = 'os-security-groups'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_security_group(self, security_group_id):
        """Get the details of a Security Group."""
        url = "os-security-groups/%s" % str(security_group_id)
        resp, body = self.get(url, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def create_security_group(self, name, description):
        """
        Creates a new security group.
        name (Required): Name of security group.
        description (Required): Description of security group.
        """
        security_group = Element("security_group", name=name)
        des = Element("description")
        des.append(Text(content=description))
        security_group.append(des)
        resp, body = self.post('os-security-groups',
                               str(Document(security_group)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_security_group(self, security_group_id):
        """Deletes the provided Security Group."""
        return self.delete('os-security-groups/%s' %
                           str(security_group_id), self.headers)

    def create_security_group_rule(self, parent_group_id, ip_proto, from_port,
                                   to_port, **kwargs):
        """
        Creating a new security group rules.
        parent_group_id :ID of Security group
        ip_protocol : ip_proto (icmp, tcp, udp).
        from_port: Port at start of range.
        to_port  : Port at end of range.
        Following optional keyword arguments are accepted:
        cidr     : CIDR for address range.
        group_id : ID of the Source group
        """
        group_rule = Element("security_group_rule")

        elements = {k: kwargs.get(k) for k in ('cidr', 'group_id')}
        elements['parent_group_id'] = parent_group_id
        elements['ip_protocol'] = ip_proto
        elements['from_port'] = from_port
        elements['to_port'] = to_port

        for k, v in elements.items():
            if v is not None:
                element = Element(k)
                element.append(Text(content=str(v)))
                group_rule.append(element)

        url = 'os-security-group-rules'
        resp, body = self.post(url, str(Document(group_rule)), self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule."""
        return self.delete('os-security-group-rules/%s' %
                           str(group_rule_id), self.headers)

    def list_security_group_rules(self, security_group_id):
        """List all rules for a security group."""
        url = "os-security-groups"
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        secgroups = body.getchildren()
        for secgroup in secgroups:
            if secgroup.get('id') == security_group_id:
                node = secgroup.find('{%s}rules' % XMLNS_11)
                rules = [xml_to_json(x) for x in node.getchildren()]
                return resp, rules
        raise exceptions.NotFound('No such Security Group')
