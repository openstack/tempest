# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
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

from urlparse import urlparse

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json


XMLNS = "http://docs.openstack.org/identity/api/v3"


class ServiceClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ServiceClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        data = xml_to_json(body)
        return data

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(ServiceClientXML, self).request(method, url,
                                                     headers=headers,
                                                     body=body)

    def update_service(self, service_id, **kwargs):
        """Updates a service_id."""
        resp, body = self.get_service(service_id)
        name = kwargs.get('name', body['name'])
        description = kwargs.get('description', body['description'])
        type = kwargs.get('type', body['type'])
        update_service = Element("service",
                                 xmlns=XMLNS,
                                 id=service_id,
                                 name=name,
                                 description=description,
                                 type=type)
        resp, body = self.patch('services/%s' % service_id,
                                str(Document(update_service)),
                                self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_service(self, service_id):
        """Get Service."""
        url = 'services/%s' % service_id
        resp, body = self.get(url, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body
