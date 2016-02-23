# Copyright 2016 Rackspace
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

import os
import shutil
import subprocess
import tempfile

from tempest.cmd.workspace import WorkspaceManager
from tempest.lib.common.utils import data_utils
from tempest.tests import base


class TestTempestWorkspaceBase(base.TestCase):
    def setUp(self):
        super(TestTempestWorkspaceBase, self).setUp()
        self.name = data_utils.rand_uuid()
        self.path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.path, ignore_errors=True)
        store_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, store_dir, ignore_errors=True)
        self.store_file = os.path.join(store_dir, 'workspace.yaml')
        self.workspace_manager = WorkspaceManager(path=self.store_file)
        self.workspace_manager.register_new_workspace(self.name, self.path)


class TestTempestWorkspace(TestTempestWorkspaceBase):
    def _run_cmd_gets_return_code(self, cmd, expected):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return_code = process.returncode
        msg = ("%s failled with:\nstdout: %s\nstderr: %s" % (' '.join(cmd),
                                                             stdout, stderr))
        self.assertEqual(return_code, expected, msg)

    def test_run_workspace_list(self):
        cmd = ['tempest', 'workspace', '--workspace-path',
               self.store_file, 'list']
        self._run_cmd_gets_return_code(cmd, 0)

    def test_run_workspace_register(self):
        name = data_utils.rand_uuid()
        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        cmd = ['tempest', 'workspace', '--workspace-path', self.store_file,
               'register', '--name', name, '--path', path]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNotNone(self.workspace_manager.get_workspace(name))

    def test_run_workspace_rename(self):
        new_name = data_utils.rand_uuid()
        cmd = ['tempest', 'workspace', '--workspace-path', self.store_file,
               'rename', "--old-name", self.name, '--new-name', new_name]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_run_workspace_move(self):
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        cmd = ['tempest', 'workspace', '--workspace-path', self.store_file,
               'move', '--name', self.name, '--path', new_path]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertEqual(
            self.workspace_manager.get_workspace(self.name), new_path)

    def test_run_workspace_remove(self):
        cmd = ['tempest', 'workspace', '--workspace-path', self.store_file,
               'remove', '--name', self.name]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))


class TestTempestWorkspaceManager(TestTempestWorkspaceBase):
    def setUp(self):
        super(TestTempestWorkspaceManager, self).setUp()
        self.name = data_utils.rand_uuid()
        self.path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.path, ignore_errors=True)
        store_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, store_dir, ignore_errors=True)
        self.store_file = os.path.join(store_dir, 'workspace.yaml')
        self.workspace_manager = WorkspaceManager(path=self.store_file)
        self.workspace_manager.register_new_workspace(self.name, self.path)

    def test_workspace_manager_get(self):
        self.assertIsNotNone(self.workspace_manager.get_workspace(self.name))

    def test_workspace_manager_rename(self):
        new_name = data_utils.rand_uuid()
        self.workspace_manager.rename_workspace(self.name, new_name)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_workspace_manager_move(self):
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        self.workspace_manager.move_workspace(self.name, new_path)
        self.assertEqual(
            self.workspace_manager.get_workspace(self.name), new_path)

    def test_workspace_manager_remove(self):
        self.workspace_manager.remove_workspace(self.name)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))

    def test_path_expansion(self):
        name = data_utils.rand_uuid()
        path = os.path.join("~", name)
        os.makedirs(os.path.expanduser(path))
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        self.workspace_manager.register_new_workspace(name, path)
        self.assertIsNotNone(self.workspace_manager.get_workspace(name))
