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

from io import StringIO
import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

from tempest.cmd import workspace
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
        self.workspace_manager = workspace.WorkspaceManager(
            path=self.store_file)
        self.workspace_manager.register_new_workspace(self.name, self.path)


class TestTempestWorkspace(TestTempestWorkspaceBase):
    def _run_cmd_gets_return_code(self, cmd, expected):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return_code = process.returncode
        msg = ("%s failed with:\nstdout: %s\nstderr: %s" % (' '.join(cmd),
                                                            stdout, stderr))
        self.assertEqual(return_code, expected, msg)

    def test_run_workspace_list(self):
        cmd = ['tempest', 'workspace', 'list',
               '--workspace-path', self.store_file]
        self._run_cmd_gets_return_code(cmd, 0)

    def test_run_workspace_register(self):
        name = data_utils.rand_uuid()
        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        cmd = ['tempest', 'workspace', 'register',
               '--workspace-path', self.store_file,
               '--name', name, '--path', path]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNotNone(self.workspace_manager.get_workspace(name))

    def test_run_workspace_rename(self):
        new_name = data_utils.rand_uuid()
        cmd = ['tempest', 'workspace', 'rename',
               '--workspace-path', self.store_file,
               '--old-name', self.name, '--new-name', new_name]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_run_workspace_move(self):
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        cmd = ['tempest', 'workspace', 'move',
               '--workspace-path', self.store_file,
               '--name', self.name, '--path', new_path]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertEqual(
            self.workspace_manager.get_workspace(self.name), new_path)

    def test_run_workspace_remove_entry(self):
        cmd = ['tempest', 'workspace', 'remove',
               '--workspace-path', self.store_file,
               '--name', self.name]
        self._run_cmd_gets_return_code(cmd, 0)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))

    def test_run_workspace_remove_directory(self):
        cmd = ['tempest', 'workspace', 'remove',
               '--workspace-path', self.store_file,
               '--name', self.name, '--rmdir']
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
        self.workspace_manager = workspace.WorkspaceManager(
            path=self.store_file)
        self.workspace_manager.register_new_workspace(self.name, self.path)

    def test_workspace_manager_get(self):
        self.assertIsNotNone(self.workspace_manager.get_workspace(self.name))

    def test_workspace_manager_rename(self):
        new_name = data_utils.rand_uuid()
        self.workspace_manager.rename_workspace(self.name, new_name)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_workspace_manager_rename_no_name_exist(self):
        no_name = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.rename_workspace,
                                   self.name, no_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "None or empty name is specified."
                         " Please specify correct name for workspace.\n")

    def test_workspace_manager_rename_with_existing_name(self):
        new_name = self.name
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.rename_workspace,
                                   self.name, new_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace already exists with name: %s.\n"
                         % new_name)

    def test_workspace_manager_rename_no_exist_old_name(self):
        old_name = ""
        new_name = data_utils.rand_uuid()
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.rename_workspace,
                                   old_name, new_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % old_name)

    def test_workspace_manager_rename_integer_data(self):
        old_name = self.name
        new_name = 12345
        self.workspace_manager.rename_workspace(old_name, new_name)
        self.assertIsNone(self.workspace_manager.get_workspace(old_name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_workspace_manager_rename_alphanumeric_data(self):
        old_name = self.name
        new_name = 'abc123'
        self.workspace_manager.rename_workspace(old_name, new_name)
        self.assertIsNone(self.workspace_manager.get_workspace(old_name))
        self.assertIsNotNone(self.workspace_manager.get_workspace(new_name))

    def test_workspace_manager_move(self):
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        self.workspace_manager.move_workspace(self.name, new_path)
        self.assertEqual(
            self.workspace_manager.get_workspace(self.name), new_path)
        # NOTE(mbindlish): Also checking for the workspace that it
        # shouldn't exist in old path
        self.assertNotEqual(
            self.workspace_manager.get_workspace(self.name), self.path)

    def test_workspace_manager_move_wrong_path(self):
        new_path = 'wrong/path'
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.move_workspace,
                                   self.name, new_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "Path does not exist.\n")

    def test_workspace_manager_move_wrong_workspace(self):
        workspace_name = "wrong_workspace_name"
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.move_workspace,
                                   workspace_name, new_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % workspace_name)

    def test_workspace_manager_move_no_workspace_name(self):
        workspace_name = ""
        new_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, new_path, ignore_errors=True)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.move_workspace,
                                   workspace_name, new_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % workspace_name)

    def test_workspace_manager_move_no_workspace_path(self):
        new_path = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.move_workspace,
                                   self.name, new_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "None or empty path is specified for workspace."
                         " Please specify correct workspace path.\n")

    def test_workspace_manager_remove_entry(self):
        self.workspace_manager.remove_workspace_entry(self.name)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))

    def test_workspace_manager_remove_entry_no_name(self):
        no_name = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   remove_workspace_entry,
                                   no_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % no_name)

    def test_workspace_manager_remove_entry_wrong_name(self):
        wrong_name = "wrong_name"
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   remove_workspace_entry,
                                   wrong_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % wrong_name)

    def test_workspace_manager_remove_directory(self):
        path = self.workspace_manager.remove_workspace_entry(self.name)
        self.workspace_manager.remove_workspace_directory(path)
        self.assertIsNone(self.workspace_manager.get_workspace(self.name))

    def test_workspace_manager_remove_directory_no_path(self):
        no_path = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   remove_workspace_directory,
                                   no_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "None or empty path is specified for workspace."
                         " Please specify correct workspace path.\n")

    def test_path_expansion(self):
        name = data_utils.rand_uuid()
        path = os.path.join("~", name)
        os.makedirs(os.path.expanduser(path))
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        self.workspace_manager.register_new_workspace(name, path)
        self.assertIsNotNone(self.workspace_manager.get_workspace(name))

    def test_workspace_name_not_exists(self):
        nonexistent_name = data_utils.rand_uuid()
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager._name_exists,
                                   nonexistent_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace was not found with name: %s\n"
                         % nonexistent_name)

    def test_workspace_name_exists(self):
        self.assertIsNone(self.workspace_manager._name_exists(self.name))

    def test_workspace_name_already_exists(self):
        duplicate_name = self.name
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   _workspace_name_exists,
                                   duplicate_name)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "A workspace already exists with name: %s.\n"
                         % duplicate_name)

    def test_workspace_name_exists_check_new_name(self):
        new_name = "fake_name"
        self.assertIsNone(self.workspace_manager.
                          _workspace_name_exists(new_name))

    def test_workspace_manager_path_not_exist(self):
        fake_path = "fake_path"
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager._validate_path,
                                   fake_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "Path does not exist.\n")

    def test_validate_path_exists(self):
        new_path = self.path
        self.assertIsNone(self.workspace_manager.
                          _validate_path(new_path))

    def test_workspace_manager_list_workspaces(self):
        listed = self.workspace_manager.list_workspaces()
        self.assertEqual(1, len(listed))
        self.assertIn(self.name, listed)
        self.assertEqual(self.path, listed.get(self.name))

    def test_register_new_workspace_no_name(self):
        no_name = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   register_new_workspace,
                                   no_name, self.path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "None or empty name is specified."
                         " Please specify correct name for workspace.\n")

    def test_register_new_workspace_no_path(self):
        no_path = ""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ex = self.assertRaises(SystemExit,
                                   self.workspace_manager.
                                   register_new_workspace,
                                   self.name, no_path)
        self.assertEqual(1, ex.code)
        self.assertEqual(mock_stdout.getvalue(),
                         "None or empty path is specified for workspace."
                         " Please specify correct workspace path.\n")

    def test_register_new_workspace_integer_data(self):
        workspace_name = 12345
        self.workspace_manager.register_new_workspace(
            workspace_name, self.path)
        self.assertIsNotNone(
            self.workspace_manager.get_workspace(workspace_name))
        self.assertEqual(
            self.workspace_manager.get_workspace(workspace_name), self.path)

    def test_register_new_workspace_alphanumeric_data(self):
        workspace_name = 'abc123'
        self.workspace_manager.register_new_workspace(
            workspace_name, self.path)
        self.assertIsNotNone(
            self.workspace_manager.get_workspace(workspace_name))
        self.assertEqual(
            self.workspace_manager.get_workspace(workspace_name), self.path)
