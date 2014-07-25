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

import jsonschema
import mock

from tempest.common.generator import base_generator
from tempest.common.generator import negative_generator
from tempest.common.generator import valid_generator
from tempest.tests import base


class TestNegativeBasicGenerator(base.TestCase):
    valid_desc = {
        "name": "list-flavors-with-detail",
        "http-method": "GET",
        "url": "flavors/detail",
        "json-schema": {
            "type": "object",
            "properties": {
                "minRam": {"type": "integer"},
                "minDisk": {"type": "integer"}
            }
        },
        "resources": ["flavor", "volume", "image"]
    }

    minimal_desc = {
        "name": "list-flavors-with-detail",
        "http-method": "GET",
        "url": "flavors/detail",
    }

    add_prop_desc = {
        "name": "list-flavors-with-detail",
        "http-method": "GET",
        "url": "flavors/detail",
        "unknown_field": [12]
    }

    invalid_json_schema_desc = {
        "name": "list-flavors-with-detail",
        "http-method": "GET",
        "url": "flavors/detail",
        "json-schema": {"type": "NotExistingType"}
    }

    def setUp(self):
        super(TestNegativeBasicGenerator, self).setUp()
        self.generator = base_generator.BasicGeneratorSet()

    def _assert_valid_jsonschema_call(self, jsonschema_mock, desc):
        self.assertEqual(jsonschema_mock.call_count, 1)
        jsonschema_mock.assert_called_with(desc, self.generator.schema)

    @mock.patch('jsonschema.validate', wraps=jsonschema.validate)
    def test_validate_schema_with_valid_input(self, jsonschema_mock):
        self.generator.validate_schema(self.valid_desc)
        self._assert_valid_jsonschema_call(jsonschema_mock, self.valid_desc)

    @mock.patch('jsonschema.validate', wraps=jsonschema.validate)
    def test_validate_schema_with_minimal_input(self, jsonschema_mock):
        self.generator.validate_schema(self.minimal_desc)
        self._assert_valid_jsonschema_call(jsonschema_mock, self.minimal_desc)

    def test_validate_schema_with_invalid_input(self):
        self.assertRaises(jsonschema.ValidationError,
                          self.generator.validate_schema, self.add_prop_desc)
        self.assertRaises(jsonschema.SchemaError,
                          self.generator.validate_schema,
                          self.invalid_json_schema_desc)


class BaseNegativeGenerator(object):
    types = ['string', 'integer', 'object']

    fake_input_str = {"type": "string",
                      "minLength": 2,
                      "maxLength": 8,
                      'results': {'gen_int': 404}}

    fake_input_int = {"type": "integer",
                      "maximum": 255,
                      "minimum": 1}

    fake_input_obj = {"type": "object",
                      "properties": {"minRam": {"type": "integer"},
                                     "diskName": {"type": "string"},
                                     "maxRam": {"type": "integer", }
                                     }
                      }

    unknown_type_schema = {
        "type": "not_defined"
    }

    def _validate_result(self, data):
        self.assertTrue(isinstance(data, list))
        for t in data:
            self.assertIsInstance(t, tuple)
            self.assertEqual(3, len(t))
            self.assertIsInstance(t[0], str)

    def test_generate_string(self):
        result = self.generator.generate(self.fake_input_str)
        self._validate_result(result)

    def test_generate_integer(self):
        result = self.generator.generate(self.fake_input_int)
        self._validate_result(result)

    def test_generate_obj(self):
        result = self.generator.generate(self.fake_input_obj)
        self._validate_result(result)

    def test_generator_mandatory_functions(self):
        for data_type in self.types:
            self.assertIn(data_type, self.generator.types_dict)

    def test_generate_with_unknown_type(self):
        self.assertRaises(TypeError, self.generator.generate,
                          self.unknown_type_schema)


class TestNegativeValidGenerator(base.TestCase, BaseNegativeGenerator):
    def setUp(self):
        super(TestNegativeValidGenerator, self).setUp()
        self.generator = valid_generator.ValidTestGenerator()

    def test_generate_valid(self):
        result = self.generator.generate_valid(self.fake_input_obj)
        self.assertIn("minRam", result)
        self.assertIsInstance(result["minRam"], int)
        self.assertIn("diskName", result)
        self.assertIsInstance(result["diskName"], str)


class TestNegativeNegativeGenerator(base.TestCase, BaseNegativeGenerator):
    def setUp(self):
        super(TestNegativeNegativeGenerator, self).setUp()
        self.generator = negative_generator.NegativeTestGenerator()
