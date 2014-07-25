# Copyright 2013 IBM Corp.
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

CONF = config.CONF


class HostsClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(HostsClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def list_hosts(self, params=None):
        """Lists all hosts."""

        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def show_host_detail(self, hostname):
        """Show detail information for the host."""

        resp, body = self.get("os-hosts/%s" % str(hostname))
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(node)]
        return resp, body

    def update_host(self, hostname, **kwargs):
        """Update a host."""

        request_body = xml_utils.Element("updates")
        if kwargs:
            for k, v in kwargs.iteritems():
                request_body.append(xml_utils.Element(k, v))
        resp, body = self.put("os-hosts/%s" % str(hostname),
                              str(xml_utils.Document(request_body)))
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def startup_host(self, hostname):
        """Startup a host."""

        resp, body = self.get("os-hosts/%s/startup" % str(hostname))
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def shutdown_host(self, hostname):
        """Shutdown a host."""

        resp, body = self.get("os-hosts/%s/shutdown" % str(hostname))
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def reboot_host(self, hostname):
        """Reboot a host."""

        resp, body = self.get("os-hosts/%s/reboot" % str(hostname))
        node = etree.fromstring(body)
        body = [xml_utils.xml_to_json(x) for x in node.getchildren()]
        return resp, body
