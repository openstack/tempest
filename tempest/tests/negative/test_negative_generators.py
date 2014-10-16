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

import copy

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

    fake_input_obj = {"type": "object",
                      "properties": {"minRam": {"type": "integer"},
                                     "diskName": {"type": "string"},
                                     "maxRam": {"type": "integer", }
                                     }
                      }

    unknown_type_schema = {
        "type": "not_defined"
    }

    class fake_test_class(object):
        def __init__(self, scenario):
            for k, v in scenario.iteritems():
                setattr(self, k, v)

    def _validate_result(self, valid_schema, invalid_schema):
        for k, v in valid_schema.iteritems():
            self.assertTrue(k in invalid_schema)

    def test_generator_mandatory_functions(self):
        for data_type in self.types:
            self.assertIn(data_type, self.generator.types_dict)

    def test_generate_with_unknown_type(self):
        self.assertRaises(TypeError, self.generator.generate_payload,
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

    def test_generate_obj(self):
        schema = self.fake_input_obj
        scenarios = self.generator.generate_scenarios(schema)
        for scenario in scenarios:
            test = self.fake_test_class(scenario)
            valid_schema = \
                valid_generator.ValidTestGenerator().generate_valid(schema)
            schema_under_test = copy.copy(valid_schema)
            expected_result = \
                self.generator.generate_payload(test, schema_under_test)
            self.assertEqual(expected_result, None)
            self._validate_result(valid_schema, schema_under_test)
