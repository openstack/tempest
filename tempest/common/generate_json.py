# Copyright 2014 Red Hat, Inc. & Deutsche Telekom AG
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

from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def generate_valid(schema):
    """
    Create a valid dictionary based on the types in a json schema.
    """
    LOG.debug("generate_valid: %s" % schema)
    schema_type = schema["type"]
    if isinstance(schema_type, list):
        # Just choose the first one since all are valid.
        schema_type = schema_type[0]
    return type_map_valid[schema_type](schema)


def generate_valid_string(schema):
    size = schema.get("minLength", 0)
    # TODO(dkr mko): handle format and pattern
    return "x" * size


def generate_valid_integer(schema):
    # TODO(dkr mko): handle multipleOf
    if "minimum" in schema:
        minimum = schema["minimum"]
        if "exclusiveMinimum" not in schema:
            return minimum
        else:
            return minimum + 1
    if "maximum" in schema:
        maximum = schema["maximum"]
        if "exclusiveMaximum" not in schema:
            return maximum
        else:
            return maximum - 1
    return 0


def generate_valid_object(schema):
    obj = {}
    for k, v in schema["properties"].iteritems():
        obj[k] = generate_valid(v)
    return obj


def generate_invalid(schema):
    """
    Generate an invalid json dictionary based on a schema.
    Only one value is mis-generated for each dictionary created.

    Any generator must return a list of tuples or a single tuple.
    The values of this tuple are:
      result[0]: Name of the test
      result[1]: json schema for the test
      result[2]: expected result of the test (can be None)
    """
    LOG.debug("generate_invalid: %s" % schema)
    schema_type = schema["type"]
    if isinstance(schema_type, list):
        if "integer" in schema_type:
            schema_type = "integer"
        else:
            raise Exception("non-integer list types not supported")
    result = []
    for generator in type_map_invalid[schema_type]:
        ret = generator(schema)
        if ret is not None:
            if isinstance(ret, list):
                result.extend(ret)
            elif isinstance(ret, tuple):
                result.append(ret)
            else:
                raise Exception("generator (%s) returns invalid result"
                                % generator)
    LOG.debug("result: %s" % result)
    return result


def _check_for_expected_result(name, schema):
    expected_result = None
    if "results" in schema:
        if name in schema["results"]:
            expected_result = schema["results"][name]
    return expected_result


def generator(fn):
    """
    Decorator for simple generators that simply return one value
    """
    def wrapped(schema):
        result = fn(schema)
        if result is not None:
            expected_result = _check_for_expected_result(fn.__name__, schema)
            return (fn.__name__, result, expected_result)
        return
    return wrapped


@generator
def gen_int(_):
    return 4


@generator
def gen_string(_):
    return "XXXXXX"


def gen_none(schema):
    # Note(mkoderer): it's not using the decorator otherwise it'd be filtered
    expected_result = _check_for_expected_result('gen_none', schema)
    return ('gen_none', None, expected_result)


@generator
def gen_str_min_length(schema):
    min_length = schema.get("minLength", 0)
    if min_length > 0:
        return "x" * (min_length - 1)


@generator
def gen_str_max_length(schema):
    max_length = schema.get("maxLength", -1)
    if max_length > -1:
        return "x" * (max_length + 1)


@generator
def gen_int_min(schema):
    if "minimum" in schema:
        minimum = schema["minimum"]
        if "exclusiveMinimum" not in schema:
            minimum -= 1
        return minimum


@generator
def gen_int_max(schema):
    if "maximum" in schema:
        maximum = schema["maximum"]
        if "exclusiveMaximum" not in schema:
            maximum += 1
        return maximum


def gen_obj_remove_attr(schema):
    invalids = []
    valid = generate_valid(schema)
    required = schema.get("required", [])
    for r in required:
        new_valid = copy.deepcopy(valid)
        del new_valid[r]
        invalids.append(("gen_obj_remove_attr", new_valid, None))
    return invalids


@generator
def gen_obj_add_attr(schema):
    valid = generate_valid(schema)
    if not schema.get("additionalProperties", True):
        new_valid = copy.deepcopy(valid)
        new_valid["$$$$$$$$$$"] = "xxx"
        return new_valid


def gen_inv_prop_obj(schema):
    LOG.debug("generate_invalid_object: %s" % schema)
    valid = generate_valid(schema)
    invalids = []
    properties = schema["properties"]

    for k, v in properties.iteritems():
        for invalid in generate_invalid(v):
            LOG.debug(v)
            new_valid = copy.deepcopy(valid)
            new_valid[k] = invalid[1]
            name = "prop_%s_%s" % (k, invalid[0])
            invalids.append((name, new_valid, invalid[2]))

    LOG.debug("generate_invalid_object return: %s" % invalids)
    return invalids


type_map_valid = {"string": generate_valid_string,
                  "integer": generate_valid_integer,
                  "object": generate_valid_object}

type_map_invalid = {"string": [gen_int,
                               gen_none,
                               gen_str_min_length,
                               gen_str_max_length],
                    "integer": [gen_string,
                                gen_none,
                                gen_int_min,
                                gen_int_max],
                    "object": [gen_obj_remove_attr,
                               gen_obj_add_attr,
                               gen_inv_prop_obj]}

schema = {"type": "object",
          "properties":
          {"name": {"type": "string"},
           "http-method": {"enum": ["GET", "PUT", "HEAD",
                                    "POST", "PATCH", "DELETE", 'COPY']},
           "url": {"type": "string"},
           "json-schema": jsonschema._utils.load_schema("draft4"),
           "resources": {"type": "array", "items": {"type": "string"}},
           "results": {"type": "object",
                       "properties": {}}
           },
          "required": ["name", "http-method", "url"],
          "additionalProperties": False,
          }


def validate_negative_test_schema(nts):
    jsonschema.validate(nts, schema)
