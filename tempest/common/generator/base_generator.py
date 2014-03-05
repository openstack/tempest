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

from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def _check_for_expected_result(name, schema):
    expected_result = None
    if "results" in schema:
        if name in schema["results"]:
            expected_result = schema["results"][name]
    return expected_result


def generator_type(*args):
    def wrapper(func):
        func.types = args
        return func
    return wrapper


def simple_generator(fn):
    """
    Decorator for simple generators that return one value
    """
    def wrapped(self, schema):
        result = fn(self, schema)
        if result is not None:
            expected_result = _check_for_expected_result(fn.__name__, schema)
            return (fn.__name__, result, expected_result)
        return
    return wrapped


class BasicGeneratorSet(object):
    _instance = None

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "http-method": {
                "enum": ["GET", "PUT", "HEAD",
                         "POST", "PATCH", "DELETE", 'COPY']
            },
            "admin_client": {"type": "boolean"},
            "url": {"type": "string"},
            "default_result_code": {"type": "integer"},
            "json-schema": jsonschema._utils.load_schema("draft4"),
            "resources": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "expected_result": {"type": "integer"}
                            }
                        }
                    ]
                }
            },
            "results": {
                "type": "object",
                "properties": {}
            }
        },
        "required": ["name", "http-method", "url"],
        "additionalProperties": False,
    }

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BasicGeneratorSet, cls).__new__(cls, *args,
                                                                  **kwargs)
        return cls._instance

    def __init__(self):
        self.types_dict = {}
        for m in dir(self):
            if callable(getattr(self, m)) and not'__' in m:
                method = getattr(self, m)
                if hasattr(method, "types"):
                    for type in method.types:
                        if type not in self.types_dict:
                            self.types_dict[type] = []
                        self.types_dict[type].append(method)

    def validate_schema(self, schema):
        jsonschema.validate(schema, self.schema)

    def generate(self, schema):
        """
        Generate an json dictionary based on a schema.
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
        if schema_type not in self.types_dict:
            raise Exception("generator (%s) doesn't support type: %s"
                            % (self.__class__.__name__, schema_type))
        for generator in self.types_dict[schema_type]:
            ret = generator(schema)
            if ret is not None:
                if isinstance(ret, list):
                    result.extend(ret)
                elif isinstance(ret, tuple):
                    result.append(ret)
                else:
                    raise Exception("generator (%s) returns invalid result: %s"
                                    % (generator, ret))
        LOG.debug("result: %s" % result)
        return result
