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

from tempest import config
import tempest.test as test
from tempest.tests import base
from tempest.tests import fake_config


class TestNegativeAutoTest(base.TestCase):
    # Fake entries
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
        self.assertGreater(len(entries), 1)
        for entry in entries:
            self.assertIsNotNone(entry[1]['_negtest_name'])

    def _check_resource_entries(self, result, entry):
        entries = [a for a in result if entry in a[0]]
        self.assertIsNotNone(entries)
        self.assertIs(len(entries), 3)
        for entry in entries:
            self.assertIsNotNone(entry[1]['resource'])

    def test_generate_scenario(self):
        scenarios = test.NegativeAutoTest.\
            generate_scenario(self.fake_input_desc)
        self.assertIsInstance(scenarios, list)
        for scenario in scenarios:
            self.assertIsInstance(scenario, tuple)
            self.assertIsInstance(scenario[0], str)
            self.assertIsInstance(scenario[1], dict)
        self._check_prop_entries(scenarios, "minRam")
        self._check_prop_entries(scenarios, "minDisk")
        self._check_resource_entries(scenarios, "inv_res")
