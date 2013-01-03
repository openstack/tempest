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
"""Sample stress test that creates a few virtual machines and then
destroys them"""


from stress.test_servers import *
from stress.basher import BasherAction
from stress.driver import *
from tempest import clients

choice_spec = [
    BasherAction(TestCreateVM(), 50,
                 kargs={'timeout': '60'}),
    BasherAction(TestKillActiveVM(), 50)
]


nova = clients.Manager()

bash_openstack(nova,
               choice_spec,
               duration=datetime.timedelta(seconds=10),
               sleep_time=1000,  # in milliseconds
               seed=None,
               test_name="simple create and delete",
               max_vms=4)
