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
from tempest.common import xml_utils
from tempest import config
from tempest import exceptions

CONF = config.CONF


class SecurityGroupsClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(SecurityGroupsClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_utils.xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_utils.xml_to_json(body)
        return json

    def list_security_groups(self, params=None):
        """List all security groups for a user."""

        url = 'os-security-groups'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_security_group(self, security_group_id):
        """Get the details of a Security Group."""
        url = "os-security-groups/%s" % str(security_group_id)
        resp, body = self.get(url)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def create_security_group(self, name, description):
        """
        Creates a new security group.
        name (Required): Name of security group.
        description (Required): Description of security group.
        """
        security_group = xml_utils.Element("security_group", name=name)
        des = xml_utils.Element("description")
        des.append(xml_utils.Text(content=description))
        security_group.append(des)
        resp, body = self.post('os-security-groups',
                               str(xml_utils.Document(security_group)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_security_group(self, security_group_id, name=None,
                              description=None):
        """
        Update a security group.
        security_group_id: a security_group to update
        name: new name of security group
        description: new description of security group
        """
        security_group = xml_utils.Element("security_group")
        if name:
            sg_name = xml_utils.Element("name")
            sg_name.append(xml_utils.Text(content=name))
            security_group.append(sg_name)
        if description:
            des = xml_utils.Element("description")
            des.append(xml_utils.Text(content=description))
            security_group.append(des)
        resp, body = self.put('os-security-groups/%s' %
                              str(security_group_id),
                              str(xml_utils.Document(security_group)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_security_group(self, security_group_id):
        """Deletes the provided Security Group."""
        return self.delete('os-security-groups/%s' % str(security_group_id))

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
        group_rule = xml_utils.Element("security_group_rule")

        elements = dict()
        elements['cidr'] = kwargs.get('cidr')
        elements['group_id'] = kwargs.get('group_id')
        elements['parent_group_id'] = parent_group_id
        elements['ip_protocol'] = ip_proto
        elements['from_port'] = from_port
        elements['to_port'] = to_port

        for k, v in elements.items():
            if v is not None:
                element = xml_utils.Element(k)
                element.append(xml_utils.Text(content=str(v)))
                group_rule.append(element)

        url = 'os-security-group-rules'
        resp, body = self.post(url, str(xml_utils.Document(group_rule)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule."""
        return self.delete('os-security-group-rules/%s' %
                           str(group_rule_id))

    def list_security_group_rules(self, security_group_id):
        """List all rules for a security group."""
        url = "os-security-groups"
        resp, body = self.get(url)
        body = etree.fromstring(body)
        secgroups = body.getchildren()
        for secgroup in secgroups:
            if secgroup.get('id') == security_group_id:
                node = secgroup.find('{%s}rules' % xml_utils.XMLNS_11)
                rules = [xml_utils.xml_to_json(x) for x in node.getchildren()]
                return resp, rules
        raise exceptions.NotFound('No such Security Group')

    def is_resource_deleted(self, id):
        try:
            self.get_security_group(id)
        except exceptions.NotFound:
            return True
        return False
