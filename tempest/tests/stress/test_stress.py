# Copyright 2013 Deutsche Telekom AG
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

import shlex
import subprocess

from tempest_lib import exceptions

from oslo_log import log as logging
from tempest.tests import base

LOG = logging.getLogger(__name__)


class StressFrameworkTest(base.TestCase):
    """Basic test for the stress test framework.
    """

    def _cmd(self, cmd, param):
        """Executes specified command."""
        cmd = ' '.join([cmd, param])
        LOG.info("running: '%s'" % cmd)
        cmd_str = cmd
        cmd = shlex.split(cmd.encode('utf-8'))
        result = ''
        result_err = ''
        try:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
            proc = subprocess.Popen(
                cmd, stdout=stdout, stderr=stderr)
            result, result_err = proc.communicate()
            if proc.returncode != 0:
                LOG.debug('error of %s:\n%s' % (cmd_str, result_err))
                raise exceptions.CommandFailed(proc.returncode,
                                               cmd,
                                               result)
        finally:
            LOG.debug('output of %s:\n%s' % (cmd_str, result))
        return proc.returncode

    def test_help_function(self):
        result = self._cmd("python", "-m tempest.cmd.run_stress -h")
        self.assertEqual(0, result)
