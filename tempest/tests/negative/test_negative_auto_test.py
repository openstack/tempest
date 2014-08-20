# Copyright 2014 Deutsche Telekom AG
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

import mock

from tempest import config
import tempest.test as test
from tempest.tests import base
from tempest.tests import fake_config


class TestNegativeAutoTest(base.TestCase):
    # Fake entries
    _interface = 'json'
    _service = 'compute'

    fake_input_desc = {"name": "list-flavors-with-detail",
                       "http-method": "GET",
                       "url": "flavors/detail",
                       "json-schema": {"type": "object",
                                       "properties":
                                       {"minRam": {"type": "integer"},
                                        "minDisk": {"type": "integer"}}
                                       },
                       "resources": ["flavor", "volume", "image"]
                       }

    def setUp(self):
        super(TestNegativeAutoTest, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

    def _check_prop_entries(self, result, entry):
        entries = [a for a in result if entry in a[0]]
        self.assertIsNotNone(entries)
        self.assertIs(len(entries), 2)
        for entry in entries:
            self.assertIsNotNone(entry[1]['schema'])

    def _check_resource_entries(self, result, entry):
        entries = [a for a in result if entry in a[0]]
        self.assertIsNotNone(entries)
        self.assertIs(len(entries), 3)
        for entry in entries:
            self.assertIsNotNone(entry[1]['resource'])

    @mock.patch('tempest.test.NegativeAutoTest.load_schema')
    def test_generate_scenario(self, open_mock):
        open_mock.return_value = self.fake_input_desc
        scenarios = test.NegativeAutoTest.\
            generate_scenario(None)

        self.assertIsInstance(scenarios, list)
        for scenario in scenarios:
            self.assertIsInstance(scenario, tuple)
            self.assertIsInstance(scenario[0], str)
            self.assertIsInstance(scenario[1], dict)
        self._check_prop_entries(scenarios, "prop_minRam")
        self._check_prop_entries(scenarios, "prop_minDisk")
        self._check_resource_entries(scenarios, "inv_res")

    def test_load_schema(self):
        json_schema = json.dumps(self.fake_input_desc)
        with mock.patch('tempest.test.open',
                        mock.mock_open(read_data=json_schema),
                        create=True):
            return_file = test.NegativeAutoTest.load_schema('filename')
            self.assertEqual(return_file, self.fake_input_desc)
        return_dict = test.NegativeAutoTest.load_schema(self.fake_input_desc)
        self.assertEqual(return_file, return_dict)
