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

from tempest.common import http
from tempest.common.rest_client import RestClientXML
from tempest import config
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v3"


class PolicyClientXML(RestClientXML):

    def __init__(self, username, password, auth_url, tenant_name=None):
        super(PolicyClientXML, self).__init__(username, password,
                                              auth_url, tenant_name)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "policy":
                array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_to_json(body)
        return json

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class RestClient."""
        dscv = CONF.identity.disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv)
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(PolicyClientXML, self).request(method, url,
                                                    headers=headers,
                                                    body=body)

    def create_policy(self, blob, type):
        """Creates a Policy."""
        create_policy = Element("policy", xmlns=XMLNS, blob=blob, type=type)
        resp, body = self.post('policies', str(Document(create_policy)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_policies(self):
        """Lists the policies."""
        resp, body = self.get('policies', self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_policy(self, policy_id):
        """Lists out the given policy."""
        url = 'policies/%s' % policy_id
        resp, body = self.get(url, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_policy(self, policy_id, **kwargs):
        """Updates a policy."""
        resp, body = self.get_policy(policy_id)
        type = kwargs.get('type')
        update_policy = Element("policy", xmlns=XMLNS, type=type)
        url = 'policies/%s' % policy_id
        resp, body = self.patch(url, str(Document(update_policy)),
                                self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_policy(self, policy_id):
        """Deletes the policy."""
        url = "policies/%s" % policy_id
        return self.delete(url)
