# Copyright 2013 OpenStack Foundation.
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
from tempest import config
from tempest.services.compute.xml.common import xml_to_json

CONF = config.CONF


class VolumeHostsClientXML(rest_client.RestClient):
    """
    Client class to send CRUD Volume Hosts API requests to a Cinder endpoint
    """
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(VolumeHostsClientXML, self).__init__(auth_provider)
        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.compute.build_interval
        self.build_timeout = CONF.compute.build_timeout

    def _parse_array(self, node):
        """
        This method is to parse the "list" response body
        Eg:

        <?xml version='1.0' encoding='UTF-8'?>
        <hosts>
        <host service-status="available" service="cinder-scheduler"/>
        <host service-status="available" service="cinder-volume"/>
        </hosts>

        This method will append the details of specified tag,
        here it is "host"
        Return value would be list of hosts as below

        [{'service-status': 'available', 'service': 'cinder-scheduler'},
         {'service-status': 'available', 'service': 'cinder-volume'}]
        """
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[0] == "host":
                array.append(xml_to_json(child))
        return array

    def list_hosts(self, params=None):
        """List all the hosts."""
        url = 'os-hosts'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = self._parse_array(etree.fromstring(body))
        return resp, body
