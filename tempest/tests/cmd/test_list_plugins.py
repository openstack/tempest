# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import subprocess

from tempest.tests import base


class TestTempestListPlugins(base.TestCase):
    def test_run_list_plugins(self):
        return_code = subprocess.call(
            ['tempest', 'list-plugins'], stdout=subprocess.PIPE)
        self.assertEqual(return_code, 0)
