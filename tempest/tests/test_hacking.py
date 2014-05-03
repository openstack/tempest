# Copyright 2014 Matthew Treinish
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

from tempest.hacking import checks
from tempest.tests import base


class HackingTestCase(base.TestCase):
    def test_no_setupclass_for_unit_tests(self):
        self.assertTrue(checks.no_setupclass_for_unit_tests(
            "  def setUpClass(cls):", './tempest/tests/fake_test.py'))
        self.assertIsNone(checks.no_setupclass_for_unit_tests(
            "  def setUpClass(cls): # noqa", './tempest/tests/fake_test.py'))
        self.assertFalse(checks.no_setupclass_for_unit_tests(
            "  def setUpClass(cls):", './tempest/api/fake_test.py'))
