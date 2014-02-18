# Copyright 2013 IBM Corporation
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

from tempest.common.rest_client import RestClientXML
from tempest import config
from tempest.services.compute.xml.common import xml_to_json

CONF = config.CONF


class HypervisorClientXML(RestClientXML):

    def __init__(self, auth_provider):
        super(HypervisorClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def _parse_array(self, node):
        return [xml_to_json(x) for x in node]

    def get_hypervisor_list(self):
        """List hypervisors information."""
        resp, body = self.get('os-hypervisors')
        hypervisors = self._parse_array(etree.fromstring(body))
        return resp, hypervisors

    def get_hypervisor_list_details(self):
        """Show detailed hypervisors information."""
        resp, body = self.get('os-hypervisors/detail')
        hypervisors = self._parse_array(etree.fromstring(body))
        return resp, hypervisors

    def get_hypervisor_show_details(self, hyper_id):
        """Display the details of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s' % hyper_id)
        hypervisor = xml_to_json(etree.fromstring(body))
        return resp, hypervisor

    def get_hypervisor_servers(self, hyper_name):
        """List instances belonging to the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/servers' % hyper_name)
        hypervisors = self._parse_array(etree.fromstring(body))
        return resp, hypervisors

    def get_hypervisor_stats(self):
        """Get hypervisor statistics over all compute nodes."""
        resp, body = self.get('os-hypervisors/statistics')
        stats = xml_to_json(etree.fromstring(body))
        return resp, stats

    def get_hypervisor_uptime(self, hyper_id):
        """Display the uptime of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/uptime' % hyper_id)
        uptime = xml_to_json(etree.fromstring(body))
        return resp, uptime

    def search_hypervisor(self, hyper_name):
        """Search specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/search' % hyper_name)
        hypervisors = self._parse_array(etree.fromstring(body))
        return resp, hypervisors
