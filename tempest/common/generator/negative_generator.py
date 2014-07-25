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

import tempest.common.generator.base_generator as base
import tempest.common.generator.valid_generator as valid
from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class NegativeTestGenerator(base.BasicGeneratorSet):
    @base.generator_type("string")
    @base.simple_generator
    def gen_int(self, _):
        return 4

    @base.generator_type("integer")
    @base.simple_generator
    def gen_string(self, _):
        return "XXXXXX"

    @base.generator_type("integer", "string")
    def gen_none(self, schema):
        # Note(mkoderer): it's not using the decorator otherwise it'd be
        # filtered
        expected_result = base._check_for_expected_result('gen_none', schema)
        return ('gen_none', None, expected_result)

    @base.generator_type("string")
    @base.simple_generator
    def gen_str_min_length(self, schema):
        min_length = schema.get("minLength", 0)
        if min_length > 0:
            return "x" * (min_length - 1)

    @base.generator_type("string")
    @base.simple_generator
    def gen_str_max_length(self, schema):
        max_length = schema.get("maxLength", -1)
        if max_length > -1:
            return "x" * (max_length + 1)

    @base.generator_type("integer")
    @base.simple_generator
    def gen_int_min(self, schema):
        if "minimum" in schema:
            minimum = schema["minimum"]
            if "exclusiveMinimum" not in schema:
                minimum -= 1
            return minimum

    @base.generator_type("integer")
    @base.simple_generator
    def gen_int_max(self, schema):
        if "maximum" in schema:
            maximum = schema["maximum"]
            if "exclusiveMaximum" not in schema:
                maximum += 1
            return maximum

    @base.generator_type("object")
    def gen_obj_remove_attr(self, schema):
        invalids = []
        valid_schema = valid.ValidTestGenerator().generate_valid(schema)
        required = schema.get("required", [])
        for r in required:
            new_valid = copy.deepcopy(valid_schema)
            del new_valid[r]
            invalids.append(("gen_obj_remove_attr", new_valid, None))
        return invalids

    @base.generator_type("object")
    @base.simple_generator
    def gen_obj_add_attr(self, schema):
        valid_schema = valid.ValidTestGenerator().generate_valid(schema)
        if not schema.get("additionalProperties", True):
            new_valid = copy.deepcopy(valid_schema)
            new_valid["$$$$$$$$$$"] = "xxx"
            return new_valid

    @base.generator_type("object")
    def gen_inv_prop_obj(self, schema):
        LOG.debug("generate_invalid_object: %s" % schema)
        valid_schema = valid.ValidTestGenerator().generate_valid(schema)
        invalids = []
        properties = schema["properties"]

        for k, v in properties.iteritems():
            for invalid in self.generate(v):
                LOG.debug(v)
                new_valid = copy.deepcopy(valid_schema)
                new_valid[k] = invalid[1]
                name = "prop_%s_%s" % (k, invalid[0])
                invalids.append((name, new_valid, invalid[2]))

        LOG.debug("generate_invalid_object return: %s" % invalids)
        return invalids
