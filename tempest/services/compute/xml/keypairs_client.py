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

from tempest.common import rest_client
from tempest.common import xml_utils
from tempest import config

CONF = config.CONF


class KeyPairsClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(KeyPairsClientXML, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def list_keypairs(self):
        resp, body = self.get("os-keypairs")
        node = etree.fromstring(body)
        body = [{'keypair': xml_utils.xml_to_json(x)} for x in
                node.getchildren()]
        return resp, body

    def get_keypair(self, key_name):
        resp, body = self.get("os-keypairs/%s" % str(key_name))
        body = xml_utils.xml_to_json(etree.fromstring(body))
        return resp, body

    def create_keypair(self, name, pub_key=None):
        doc = xml_utils.Document()

        keypair_element = xml_utils.Element("keypair")

        if pub_key:
            public_key_element = xml_utils.Element("public_key")
            public_key_text = xml_utils.Text(pub_key)
            public_key_element.append(public_key_text)
            keypair_element.append(public_key_element)

        name_element = xml_utils.Element("name")
        name_text = xml_utils.Text(name)
        name_element.append(name_text)
        keypair_element.append(name_element)

        doc.append(keypair_element)

        resp, body = self.post("os-keypairs", body=str(doc))
        body = xml_utils.xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_keypair(self, key_name):
        return self.delete("os-keypairs/%s" % str(key_name))
