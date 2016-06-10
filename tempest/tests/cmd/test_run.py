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

import argparse
import os
import shutil
import subprocess
import tempfile

import mock

from tempest.cmd import run
from tempest.tests import base

DEVNULL = open(os.devnull, 'wb')


class TestTempestRun(base.TestCase):

    def setUp(self):
        super(TestTempestRun, self).setUp()
        self.run_cmd = run.TempestRun(None, None)

    def test_build_options(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, "subunit", True)
        setattr(args, "parallel", False)
        setattr(args, "concurrency", 10)
        options = self.run_cmd._build_options(args)
        self.assertEqual(['--subunit',
                          '--concurrency=10'],
                         options)

    def test__build_regex_default(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, 'smoke', False)
        setattr(args, 'regex', '')
        self.assertEqual('', self.run_cmd._build_regex(args))

    def test__build_regex_smoke(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, "smoke", True)
        setattr(args, 'regex', '')
        self.assertEqual('smoke', self.run_cmd._build_regex(args))

    def test__build_regex_regex(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, 'smoke', False)
        setattr(args, "regex", 'i_am_a_fun_little_regex')
        self.assertEqual('i_am_a_fun_little_regex',
                         self.run_cmd._build_regex(args))


class TestRunReturnCode(base.TestCase):
    def setUp(self):
        super(TestRunReturnCode, self).setUp()
        # Setup test dirs
        self.directory = tempfile.mkdtemp(prefix='tempest-unit')
        self.addCleanup(shutil.rmtree, self.directory)
        self.test_dir = os.path.join(self.directory, 'tests')
        os.mkdir(self.test_dir)
        # Setup Test files
        self.testr_conf_file = os.path.join(self.directory, '.testr.conf')
        self.setup_cfg_file = os.path.join(self.directory, 'setup.cfg')
        self.passing_file = os.path.join(self.test_dir, 'test_passing.py')
        self.failing_file = os.path.join(self.test_dir, 'test_failing.py')
        self.init_file = os.path.join(self.test_dir, '__init__.py')
        self.setup_py = os.path.join(self.directory, 'setup.py')
        shutil.copy('tempest/tests/files/testr-conf', self.testr_conf_file)
        shutil.copy('tempest/tests/files/passing-tests', self.passing_file)
        shutil.copy('tempest/tests/files/failing-tests', self.failing_file)
        shutil.copy('setup.py', self.setup_py)
        shutil.copy('tempest/tests/files/setup.cfg', self.setup_cfg_file)
        shutil.copy('tempest/tests/files/__init__.py', self.init_file)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)

    def assertRunExit(self, cmd, expected):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        msg = ("Running %s got an unexpected returncode\n"
               "Stdout: %s\nStderr: %s" % (' '.join(cmd), out, err))
        self.assertEqual(p.returncode, expected, msg)

    def test_tempest_run_passes(self):
        # Git init is required for the pbr testr command. pbr requires a git
        # version or an sdist to work. so make the test directory a git repo
        # too.
        subprocess.call(['git', 'init'], stderr=DEVNULL)
        self.assertRunExit(['tempest', 'run', '--regex', 'passing'], 0)

    def test_tempest_run_fails(self):
        # Git init is required for the pbr testr command. pbr requires a git
        # version or an sdist to work. so make the test directory a git repo
        # too.
        subprocess.call(['git', 'init'], stderr=DEVNULL)
        self.assertRunExit(['tempest', 'run'], 1)
