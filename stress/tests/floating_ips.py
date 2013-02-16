# Copyright 2011 Quanta Research Cambridge, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""Stress test that associates/disasssociates floating ips."""

import datetime

from stress.basher import BasherAction
from stress.driver import bash_openstack
from stress.test_floating_ips import TestChangeFloatingIp
from tempest import clients


choice_spec = [
    BasherAction(TestChangeFloatingIp(), 100)
]

nova = clients.Manager()

bash_openstack(nova,
               choice_spec,
               duration=datetime.timedelta(seconds=300),
               test_name="floating_ips",
               initial_floating_ips=8,
               initial_vms=8)
