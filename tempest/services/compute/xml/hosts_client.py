# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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
from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import xml_to_json


class HostsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(HostsClientXML, self).__init__(config, username, password,
                                             auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_hosts(self, params=None):
        """Lists all hosts."""

        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        node = etree.fromstring(body)
        body = [xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def show_host_detail(self, hostname):
        """Show detail information for the host."""

        resp, body = self.get("os-hosts/%s" % str(hostname), self.headers)
        node = etree.fromstring(body)
        body = [xml_to_json(x) for x in node.getchildren()]
        return resp, body
