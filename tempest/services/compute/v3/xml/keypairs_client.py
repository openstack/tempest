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
from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json


class KeyPairsV3ClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(KeyPairsV3ClientXML, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.compute.catalog_v3_type

    def list_keypairs(self):
        resp, body = self.get("keypairs", self.headers)
        node = etree.fromstring(body)
        body = [{'keypair': xml_to_json(x)} for x in node.getchildren()]
        return resp, body

    def get_keypair(self, key_name):
        resp, body = self.get("keypairs/%s" % str(key_name), self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def create_keypair(self, name, pub_key=None):
        doc = Document()

        keypair_element = Element("keypair")

        if pub_key:
            public_key_element = Element("public_key")
            public_key_text = Text(pub_key)
            public_key_element.append(public_key_text)
            keypair_element.append(public_key_element)

        name_element = Element("name")
        name_text = Text(name)
        name_element.append(name_text)
        keypair_element.append(name_element)

        doc.append(keypair_element)

        resp, body = self.post("keypairs",
                               headers=self.headers, body=str(doc))
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_keypair(self, key_name):
        return self.delete("keypairs/%s" % str(key_name))
