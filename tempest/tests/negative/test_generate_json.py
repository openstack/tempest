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

from tempest.common.generator import negative_generator
import tempest.test


class TestNegativeGenerator(tempest.test.BaseTestCase):

    fake_input_str = {"type": "string",
                      "minLength": 2,
                      "maxLength": 8,
                      'results': {'gen_number': 404}}

    fake_input_int = {"type": "integer",
                      "maximum": 255,
                      "minimum": 1}

    fake_input_obj = {"type": "object",
                      "properties": {"minRam": {"type": "integer"},
                                     "diskName": {"type": "string"},
                                     "maxRam": {"type": "integer", }
                                     }
                      }

    def setUp(self):
        super(TestNegativeGenerator, self).setUp()
        self.negative = negative_generator.NegativeTestGenerator()

    def _validate_result(self, data):
        self.assertTrue(isinstance(data, list))
        for t in data:
            self.assertTrue(isinstance(t, tuple))

    def test_generate_invalid_string(self):
        result = self.negative.generate(self.fake_input_str)
        self._validate_result(result)

    def test_generate_invalid_integer(self):
        result = self.negative.generate(self.fake_input_int)
        self._validate_result(result)

    def test_generate_invalid_obj(self):
        result = self.negative.generate(self.fake_input_obj)
        self._validate_result(result)
