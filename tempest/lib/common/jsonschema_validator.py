# Copyright 2016 NEC Corporation.
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
from oslo_serialization import base64
from oslo_utils import timeutils

# JSON Schema validator and format checker used for JSON Schema validation
JSONSCHEMA_VALIDATOR = jsonschema.Draft4Validator
FORMAT_CHECKER = jsonschema.draft4_format_checker


# NOTE(gmann): Add customized format checker for 'date-time' format because:
# 1. jsonschema needs strict_rfc3339 or isodate module to be installed
#    for proper date-time checking as per rfc3339.
# 2. Nova or other OpenStack components handle the date time format as
#    ISO 8601 which is defined in oslo_utils.timeutils
# so this checker will validate the date-time as defined in
# oslo_utils.timeutils
@FORMAT_CHECKER.checks('iso8601-date-time')
def _validate_datetime_format(instance):
    try:
        if isinstance(instance, jsonschema.compat.str_types):
            timeutils.parse_isotime(instance)
    except ValueError:
        return False
    else:
        return True


@jsonschema.FormatChecker.cls_checks('base64')
def _validate_base64_format(instance):
    try:
        if isinstance(instance, str):
            instance = instance.encode('utf-8')
        base64.decode_as_bytes(instance)
    except TypeError:
        # The name must be string type. If instance isn't string type, the
        # TypeError will be raised at here.
        return False

    return True
