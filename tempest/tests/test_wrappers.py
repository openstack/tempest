# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import shutil
import subprocess
import tempfile
import testtools

from tempest.test import attr

DEVNULL = open(os.devnull, 'wb')


class TestWrappers(testtools.TestCase):
    def setUp(self):
        super(TestWrappers, self).setUp()
        # Setup test dirs
        self.directory = tempfile.mkdtemp(prefix='tempest-unit')
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

    @attr(type='smoke')
    def test_pretty_tox(self):
        # Copy wrapper script and requirements:
        pretty_tox = os.path.join(self.directory, 'pretty_tox.sh')
        shutil.copy('tools/pretty_tox.sh', pretty_tox)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)
        # Git init is required for the pbr testr command. pbr requires a git
        # version or an sdist to work. so make the test directory a git repo
        # too.
        subprocess.call(['git', 'init'])
        exit_code = subprocess.call('sh pretty_tox.sh tests.passing',
                                    shell=True, stdout=DEVNULL, stderr=DEVNULL)
        self.assertEqual(exit_code, 0)

    @attr(type='smoke')
    def test_pretty_tox_fails(self):
        # Copy wrapper script and requirements:
        pretty_tox = os.path.join(self.directory, 'pretty_tox.sh')
        shutil.copy('tools/pretty_tox.sh', pretty_tox)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)
        # Git init is required for the pbr testr command. pbr requires a git
        # version or an sdist to work. so make the test directory a git repo
        # too.
        subprocess.call(['git', 'init'])
        exit_code = subprocess.call('sh pretty_tox.sh', shell=True,
                                    stdout=DEVNULL, stderr=DEVNULL)
        self.assertEqual(exit_code, 1)

    @attr(type='smoke')
    def test_pretty_tox_serial(self):
        # Copy wrapper script and requirements:
        pretty_tox = os.path.join(self.directory, 'pretty_tox_serial.sh')
        shutil.copy('tools/pretty_tox_serial.sh', pretty_tox)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)
        exit_code = subprocess.call('sh pretty_tox_serial.sh tests.passing',
                                    shell=True, stdout=DEVNULL, stderr=DEVNULL)
        self.assertEqual(exit_code, 0)

    @attr(type='smoke')
    def test_pretty_tox_serial_fails(self):
        # Copy wrapper script and requirements:
        pretty_tox = os.path.join(self.directory, 'pretty_tox_serial.sh')
        shutil.copy('tools/pretty_tox_serial.sh', pretty_tox)
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)
        exit_code = subprocess.call('sh pretty_tox_serial.sh', shell=True,
                                    stdout=DEVNULL, stderr=DEVNULL)
        self.assertEqual(exit_code, 1)
