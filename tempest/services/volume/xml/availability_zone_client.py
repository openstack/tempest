# Copyright 2014 NEC Corporation
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


class BaseVolumeAvailabilityZoneClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(BaseVolumeAvailabilityZoneClientXML, self).__init__(
            auth_provider)
        self.service = CONF.volume.catalog_type

    def _parse_array(self, node):
        return [xml_utils.xml_to_json(x) for x in node]

    def get_availability_zone_list(self):
        resp, body = self.get('os-availability-zone')
        availability_zone = self._parse_array(etree.fromstring(body))
        self.expected_success(200, resp.status)
        return resp, availability_zone


class VolumeAvailabilityZoneClientXML(BaseVolumeAvailabilityZoneClientXML):
    """
    Volume V1 availability zone client.
    """
