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
import re

RE_OWNER = re.compile('^network:.*router_.*interface.*')


def _is_owner_router_interface(owner):
    return bool(RE_OWNER.match(owner))


def is_router_interface_port(port):
    """Based on the port attributes determines is it a router interface."""
    return _is_owner_router_interface(port['device_owner'])
