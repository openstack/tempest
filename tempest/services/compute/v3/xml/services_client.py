# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
# Copyright 2013 IBM Corp.
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


class ServicesV3ClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ServicesV3ClientXML, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.compute.catalog_v3_type

    def list_services(self, params=None):
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        node = etree.fromstring(body)
        body = [xml_to_json(x) for x in node.getchildren()]
        return resp, body

    def enable_service(self, host_name, binary):
        """
        Enable service on a host
        host_name: Name of host
        binary: Service binary
        """
        post_body = Element("service")
        post_body.add_attr('binary', binary)
        post_body.add_attr('host', host_name)

        resp, body = self.put('os-services/enable', str(Document(post_body)),
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def disable_service(self, host_name, binary):
        """
        Disable service on a host
        host_name: Name of host
        binary: Service binary
        """
        post_body = Element("service")
        post_body.add_attr('binary', binary)
        post_body.add_attr('host', host_name)

        resp, body = self.put('os-services/disable', str(Document(post_body)),
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body
