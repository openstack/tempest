# Copyright (c) 2015 Deutsche Telekom AG
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

from tempest.test_discover import plugins


class FakePlugin(plugins.TempestPlugin):
    expected_load_test = ["my/test/path", "/home/dir"]

    def load_tests(self):
        return self.expected_load_test

    def register_opts(self, conf):
        return

    def get_opt_lists(self):
        return []


class FakeStevedoreObj(object):
    obj = FakePlugin()

    @property
    def name(self):
        return self._name

    def __init__(self, name='Test1'):
        self._name = name
