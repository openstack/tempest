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

from tempest.lib import exceptions
from tempest.tests import base


class TestOutputParser(base.TestCase):

    def test_command_failed_exception(self):
        returncode = 1
        cmd = "foo"
        stdout = "output"
        stderr = "error"
        try:
            raise exceptions.CommandFailed(returncode, cmd, stdout, stderr)
        except exceptions.CommandFailed as e:
            self.assertIn(str(returncode), str(e))
            self.assertIn(cmd, str(e))
            self.assertIn(stdout, str(e))
            self.assertIn(stderr, str(e))
