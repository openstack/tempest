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
import atexit
import os
import shutil
import subprocess
import tempfile

import fixtures
import mock
import six

from tempest.cmd import run
from tempest.tests import base

DEVNULL = open(os.devnull, 'wb')
atexit.register(DEVNULL.close)


class TestTempestRun(base.TestCase):

    def setUp(self):
        super(TestTempestRun, self).setUp()
        self.run_cmd = run.TempestRun(None, None)

    def test__build_regex_default(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, 'smoke', False)
        setattr(args, 'regex', '')
        self.assertIsNone(None, self.run_cmd._build_regex(args))

    def test__build_regex_smoke(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, "smoke", True)
        setattr(args, 'regex', '')
        self.assertEqual(['smoke'], self.run_cmd._build_regex(args))

    def test__build_regex_regex(self):
        args = mock.Mock(spec=argparse.Namespace)
        setattr(args, 'smoke', False)
        setattr(args, "regex", 'i_am_a_fun_little_regex')
        self.assertEqual(['i_am_a_fun_little_regex'],
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
        self.stestr_conf_file = os.path.join(self.directory, '.stestr.conf')
        self.setup_cfg_file = os.path.join(self.directory, 'setup.cfg')
        self.passing_file = os.path.join(self.test_dir, 'test_passing.py')
        self.failing_file = os.path.join(self.test_dir, 'test_failing.py')
        self.init_file = os.path.join(self.test_dir, '__init__.py')
        self.setup_py = os.path.join(self.directory, 'setup.py')
        shutil.copy('tempest/tests/files/testr-conf', self.stestr_conf_file)
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
        return out, err

    def test_tempest_run_passes(self):
        self.assertRunExit(['tempest', 'run', '--regex', 'passing'], 0)

    def test_tempest_run_passes_with_stestr_repository(self):
        subprocess.call(['stestr', 'init'])
        self.assertRunExit(['tempest', 'run', '--regex', 'passing'], 0)

    def test_tempest_run_fails(self):
        self.assertRunExit(['tempest', 'run'], 1)

    def test_run_list(self):
        subprocess.call(['stestr', 'init'])
        out, err = self.assertRunExit(['tempest', 'run', '-l'], 0)
        tests = out.split()
        tests = sorted([six.text_type(x.rstrip()) for x in tests if x])
        result = [
            six.text_type('tests.test_failing.FakeTestClass.test_pass'),
            six.text_type('tests.test_failing.FakeTestClass.test_pass_list'),
            six.text_type('tests.test_passing.FakeTestClass.test_pass'),
            six.text_type('tests.test_passing.FakeTestClass.test_pass_list'),
        ]
        # NOTE(mtreinish): on python 3 the subprocess prints b'' around
        # stdout.
        if six.PY3:
            result = ["b\'" + x + "\'" for x in result]
        self.assertEqual(result, tests)

    def test_tempest_run_with_whitelist(self):
        fd, path = tempfile.mkstemp()
        self.addCleanup(os.remove, path)
        whitelist_file = os.fdopen(fd, 'wb', 0)
        self.addCleanup(whitelist_file.close)
        whitelist_file.write('passing'.encode('utf-8'))
        self.assertRunExit(['tempest', 'run', '--whitelist-file=%s' % path], 0)

    def test_tempest_run_with_whitelist_with_regex(self):
        fd, path = tempfile.mkstemp()
        self.addCleanup(os.remove, path)
        whitelist_file = os.fdopen(fd, 'wb', 0)
        self.addCleanup(whitelist_file.close)
        whitelist_file.write('passing'.encode('utf-8'))
        self.assertRunExit(['tempest', 'run', '--whitelist-file=%s' % path,
                            '--regex', 'fail'], 1)

    def test_tempest_run_passes_with_config_file(self):
        self.assertRunExit(['tempest', 'run',
                            '--config-file', self.stestr_conf_file,
                            '--regex', 'passing'], 0)


class TestTakeAction(base.TestCase):
    def test_workspace_not_registered(self):
        class Exception_(Exception):
            pass

        m_exit = self.useFixture(fixtures.MockPatch('sys.exit')).mock
        # sys.exit must not continue (or exit)
        m_exit.side_effect = Exception_

        workspace = self.getUniqueString()

        tempest_run = run.TempestRun(app=mock.Mock(), app_args=mock.Mock())
        parsed_args = mock.Mock()
        parsed_args.config_file = []

        # Override $HOME so that empty workspace gets created in temp dir.
        self.useFixture(fixtures.TempHomeDir())

        # Force use of the temporary home directory.
        parsed_args.workspace_path = None

        # Simulate --workspace argument.
        parsed_args.workspace = workspace

        self.assertRaises(Exception_, tempest_run.take_action, parsed_args)
        exit_msg = m_exit.call_args[0][0]
        self.assertIn(workspace, exit_msg)

    def test_config_file_specified(self):
        # Setup test dirs
        self.directory = tempfile.mkdtemp(prefix='tempest-unit')
        self.addCleanup(shutil.rmtree, self.directory)
        self.test_dir = os.path.join(self.directory, 'tests')
        os.mkdir(self.test_dir)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)

        tempest_run = run.TempestRun(app=mock.Mock(), app_args=mock.Mock())
        parsed_args = mock.Mock()

        parsed_args.workspace = None
        parsed_args.state = None
        parsed_args.list_tests = False
        parsed_args.config_file = '.stestr.conf'

        with mock.patch('stestr.commands.run_command') as m:
            m.return_value = 0
            self.assertEqual(0, tempest_run.take_action(parsed_args))
            m.assert_called()
