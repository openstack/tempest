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

from oslo_log import log

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest import test

LOG = log.getLogger(__name__)


class AgentsAdminTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Agents API"""
    
    def test_printing(msg):
        msg = "New Function to test"
        print(msg)
       
    if __name__ == '__main__':
             test_printing("mytest")
