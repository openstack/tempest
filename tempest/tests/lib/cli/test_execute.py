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


from tempest.lib.cli import base as cli_base
from tempest.lib import exceptions
from tempest.tests import base


class TestExecute(base.TestCase):
    def test_execute_success(self):
        result = cli_base.execute("/bin/ls", action="tempest",
                                  flags="-l -a")
        self.assertIsInstance(result, str)
        self.assertIn("__init__.py", result)

    def test_execute_failure(self):
        result = cli_base.execute("/bin/ls", action="tempest.lib",
                                  flags="--foobar", merge_stderr=True,
                                  fail_ok=True)
        self.assertIsInstance(result, str)
        self.assertIn("--foobar", result)

    def test_execute_failure_raise_exception(self):
        self.assertRaises(exceptions.CommandFailed, cli_base.execute,
                          "/bin/ls", action="tempest", flags="--foobar",
                          merge_stderr=True)
