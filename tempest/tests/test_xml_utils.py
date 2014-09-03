#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.common import xml_utils
from tempest.tests import base


class TestDocumentXML(base.TestCase):
    def test_xml_document_ordering_version_encoding(self):
        expected = '<?xml version="1.0" encoding="UTF-8"?>'
        xml_out = str(xml_utils.Document())
        self.assertEqual(expected, xml_out.strip())

        xml_out = str(xml_utils.Document(encoding='UTF-8', version='1.0'))
        self.assertEqual(expected, xml_out.strip())

        xml_out = str(xml_utils.Document(version='1.0', encoding='UTF-8'))
        self.assertEqual(expected, xml_out.strip())

    def test_xml_document_additonal_attrs(self):
        expected = '<?xml version="1.0" encoding="UTF-8" foo="bar"?>'
        xml_out = str(xml_utils.Document(foo='bar'))
        self.assertEqual(expected, xml_out.strip())
