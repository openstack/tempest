# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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

"""
Functional test case to check the status of gepetto and
set information of hosts etc..
"""

import os
from kong import tests


class TestSkipExamples(tests.FunctionalTest):
    @tests.skip_test("testing skipping")
    def test_absolute_skip(self):
        x = 1

    @tests.skip_unless(os.getenv("BLAH"),
           "Skipping -- Environment variable BLAH does not exist")
    def test_skip_unless_env_blah_exists(self):
        x = 1

    @tests.skip_unless(os.getenv("USER"),
           "Not Skipping -- Environment variable USER does not exist")
    def test_skip_unless_env_user_exists(self):
        x = 1

    @tests.skip_if(os.getenv("USER"),
           "Skiping -- Environment variable USER exists")
    def test_skip_if_env_user_exists(self):
        x = 1

    @tests.skip_if(os.getenv("BLAH"),
           "Not Skipping -- Environment variable BLAH exists")
    def test_skip_if_env_blah_exists(self):
        x = 1

    def test_tags_example(self):
        pass
    test_tags_example.tags = ['kvm', 'olympus']
