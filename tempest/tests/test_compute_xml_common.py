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
from lxml import etree

from tempest.common import xml_utils as common
from tempest.tests import base


class TestXMLParser(base.TestCase):

    def test_xml_to_json_parser_bool_value(self):
        node = etree.fromstring('''<health_monitor
        xmlns="http://openstack.org/quantum/api/v2.0"
         xmlns:quantum="http://openstack.org/quantum/api/v2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
           <admin_state_up quantum:type="bool">False</admin_state_up>
          <fake_state_up quantum:type="bool">True</fake_state_up>
          </health_monitor>''')
        body = common.xml_to_json(node)
        self.assertEqual(body['admin_state_up'], False)
        self.assertEqual(body['fake_state_up'], True)

    def test_xml_to_json_parser_int_value(self):
        node = etree.fromstring('''<health_monitor
        xmlns="http://openstack.org/quantum/api/v2.0"
         xmlns:quantum="http://openstack.org/quantum/api/v2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <delay quantum:type="long">4</delay>
          <max_retries quantum:type="int">3</max_retries>
          </health_monitor>''')
        body = common.xml_to_json(node)
        self.assertEqual(body['delay'], 4L)
        self.assertEqual(body['max_retries'], 3)

    def test_xml_to_json_parser_text_value(self):
        node = etree.fromstring('''<health_monitor
        xmlns="http://openstack.org/quantum/api/v2.0"
         xmlns:quantum="http://openstack.org/quantum/api/v2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <status>ACTIVE</status>
          </health_monitor>''')
        body = common.xml_to_json(node)
        self.assertEqual(body['status'], 'ACTIVE')

    def test_xml_to_json_parser_list_as_value(self):
        node = etree.fromstring('''<health_monitor
        xmlns="http://openstack.org/quantum/api/v2.0"
         xmlns:quantum="http://openstack.org/quantum/api/v2.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <elements>
          <element>first_element</element>
          <element>second_element</element>
          </elements>
          </health_monitor>''')
        body = common.xml_to_json(node, 'elements')
        self.assertEqual(body['elements'], ['first_element', 'second_element'])
