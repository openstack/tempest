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

import re
import subprocess

from tempest.tests import base


class TestTestList(base.TestCase):

    def test_no_import_errors(self):
        import_failures = []
        p = subprocess.Popen(['testr', 'list-tests'], stdout=subprocess.PIPE)
        ids = p.stdout.read()
        ids = ids.split('\n')
        for test_id in ids:
            if re.match('(\w+\.){3}\w+', test_id):
                if not test_id.startswith('tempest.'):
                    fail_id = test_id.split('unittest.loader.ModuleImport'
                                            'Failure.')[1]
                    import_failures.append(fail_id)
        error_message = ("The following tests have import failures and aren't"
                         " being run with test filters %s" % import_failures)
        self.assertFalse(import_failures, error_message)
