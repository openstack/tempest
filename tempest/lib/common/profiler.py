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

import base64
import hashlib
import hmac
import json

from oslo_utils import encodeutils
from oslo_utils import uuidutils

_profiler = {}


def enable(profiler_key, trace_id=None):
    """Enable global profiler instance

    :param profiler_key: the secret key used to enable profiling in services
    :param trace_id: unique id of the trace, if empty the id is generated
        automatically
    """
    _profiler['key'] = profiler_key
    _profiler['uuid'] = trace_id or uuidutils.generate_uuid()


def disable():
    """Disable global profiler instance"""
    _profiler.clear()


def serialize_as_http_headers():
    """Serialize profiler state as HTTP headers

    This function corresponds to the one from osprofiler library.
    :return: dictionary with 2 keys `X-Trace-Info` and `X-Trace-HMAC`.
    """
    p = _profiler
    if not p:  # profiler is not enabled
        return {}

    info = {'base_id': p['uuid'], 'parent_id': p['uuid']}
    trace_info = base64.urlsafe_b64encode(
        encodeutils.to_utf8(json.dumps(info)))
    trace_hmac = _sign(trace_info, p['key'])

    return {
        'X-Trace-Info': trace_info,
        'X-Trace-HMAC': trace_hmac,
    }


def _sign(trace_info, key):
    h = hmac.new(encodeutils.to_utf8(key), digestmod=hashlib.sha1)
    h.update(trace_info)
    return h.hexdigest()
