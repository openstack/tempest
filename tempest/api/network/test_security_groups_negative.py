# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

from tempest.api.network import test_security_groups as base
from tempest import exceptions
from tempest.test import attr
import uuid


class NegativeSecGroupTest(base.SecGroupTest):
    _interface = 'json'

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_security_group(self):
        non_exist_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.show_security_group,
                          non_exist_id)

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_security_group_rule(self):
        non_exist_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.show_security_group_rule,
                          non_exist_id)


class NegativeSecGroupTestXML(NegativeSecGroupTest):
    _interface = 'xml'
