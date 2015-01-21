# Copyright 2013 IBM Corp.
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

import os
import re
import subprocess

from tempest.tests import base


class TestTestList(base.TestCase):

    def test_testr_list_tests_no_errors(self):
        # Remove unit test discover path from env to test tempest tests
        test_env = os.environ.copy()
        test_env.pop('OS_TEST_PATH')
        import_failures = []
        p = subprocess.Popen(['testr', 'list-tests'], stdout=subprocess.PIPE,
                             env=test_env)
        ids, err = p.communicate()
        self.assertEqual(0, p.returncode,
                         "test discovery failed, one or more files cause an "
                         "error on import %s" % ids)
        ids = ids.split('\n')
        for test_id in ids:
            if re.match('(\w+\.){3}\w+', test_id):
                if not test_id.startswith('tempest.'):
                    parts = test_id.partition('tempest')
                    fail_id = parts[1] + parts[2]
                    import_failures.append(fail_id)
        error_message = ("The following tests have import failures and aren't"
                         " being run with test filters %s" % import_failures)
        self.assertFalse(import_failures, error_message)
