# Copyright 2014 Red Hat, Inc & Deutsche Telekom AG
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


from tempest.api.compute import base
from tempest import test


load_tests = test.NegativeAutoTest.load_tests


class GetConsoleOutputNegativeTestJSON(base.BaseV2ComputeTest,
                                       test.NegativeAutoTest):
    _service = 'compute'
    _schema_file = 'compute/servers/get_console_output.json'

    @classmethod
    def setUpClass(cls):
        super(GetConsoleOutputNegativeTestJSON, cls).setUpClass()
        _resp, server = cls.create_test_server()
        cls.set_resource("server", server['id'])

    @test.attr(type=['negative', 'gate'])
    def test_get_console_output(self):
        self.execute(self._schema_file)
