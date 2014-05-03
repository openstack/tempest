# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.api_schema.compute import hosts


startup_host = {
    'status_code': [200],
    'response_body': hosts.common_start_up_body
}

# The 'power_action' attribute of 'shutdown_host' API is 'shutdown'
shutdown_host = copy.deepcopy(startup_host)

shutdown_host['response_body']['properties']['power_action'] = {
    'enum': ['shutdown']
}

# The 'power_action' attribute of 'reboot_host' API is 'reboot'
reboot_host = copy.deepcopy(startup_host)

reboot_host['response_body']['properties']['power_action'] = {
    'enum': ['reboot']
}
