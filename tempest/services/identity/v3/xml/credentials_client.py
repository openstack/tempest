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

import json

from lxml import etree

from tempest.common import rest_client
from tempest import config
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v3"


class CredentialsClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(CredentialsClientXML, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'
        self.api_version = "v3"

    def _parse_body(self, body):
        data = xml_to_json(body)
        return data

    def _parse_creds(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "credential":
                array.append(xml_to_json(child))
        return array

    def create_credential(self, access_key, secret_key, user_id, project_id):
        """Creates a credential."""
        cred_type = 'ec2'
        access = "&quot;access&quot;: &quot;%s&quot;" % access_key
        secret = "&quot;secret&quot;: &quot;%s&quot;" % secret_key
        blob = Element('blob',
                       xmlns=XMLNS)
        blob.append(Text("{%s , %s}"
                         % (access, secret)))
        credential = Element('credential', project_id=project_id,
                             type=cred_type, user_id=user_id)
        credential.append(blob)
        resp, body = self.post('credentials', str(Document(credential)))
        body = self._parse_body(etree.fromstring(body))
        body['blob'] = json.loads(body['blob'])
        return resp, body

    def update_credential(self, credential_id, **kwargs):
        """Updates a credential."""
        resp, body = self.get_credential(credential_id)
        cred_type = kwargs.get('type', body['type'])
        access_key = kwargs.get('access_key', body['blob']['access'])
        secret_key = kwargs.get('secret_key', body['blob']['secret'])
        project_id = kwargs.get('project_id', body['project_id'])
        user_id = kwargs.get('user_id', body['user_id'])
        access = "&quot;access&quot;: &quot;%s&quot;" % access_key
        secret = "&quot;secret&quot;: &quot;%s&quot;" % secret_key
        blob = Element('blob',
                       xmlns=XMLNS)
        blob.append(Text("{%s , %s}"
                         % (access, secret)))
        credential = Element('credential', project_id=project_id,
                             type=cred_type, user_id=user_id)
        credential.append(blob)
        resp, body = self.patch('credentials/%s' % credential_id,
                                str(Document(credential)))
        body = self._parse_body(etree.fromstring(body))
        body['blob'] = json.loads(body['blob'])
        return resp, body

    def get_credential(self, credential_id):
        """To GET Details of a credential."""
        resp, body = self.get('credentials/%s' % credential_id)
        body = self._parse_body(etree.fromstring(body))
        body['blob'] = json.loads(body['blob'])
        return resp, body

    def list_credentials(self):
        """Lists out all the available credentials."""
        resp, body = self.get('credentials')
        body = self._parse_creds(etree.fromstring(body))
        return resp, body

    def delete_credential(self, credential_id):
        """Deletes a credential."""
        resp, body = self.delete('credentials/%s' % credential_id)
        return resp, body
