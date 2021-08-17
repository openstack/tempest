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

import ast
import importlib
import os
import shutil
import sys
import tempfile
from unittest import mock

from tempest.lib.cmd import check_uuid
from tempest.tests import base


class TestCLInterface(base.TestCase):
    CODE = "import unittest\n" \
           "class TestClass(unittest.TestCase):\n" \
           "    def test_tests(self):\n" \
           "        pass"

    def create_tests_file(self, directory):
        init_file = open(directory + "/__init__.py", "w")
        init_file.close()

        tests_file = directory + "/tests.py"
        with open(tests_file, "w") as fake_file:
            fake_file.write(TestCLInterface.CODE)
            fake_file.close()

        return tests_file

    def test_fix_argument_no(self):
        temp_dir = tempfile.mkdtemp(prefix='check-uuid-no', dir=".")
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        tests_file = self.create_tests_file(temp_dir)
        sys.argv = [sys.argv[0]] + ["--package",
                                    os.path.relpath(temp_dir)]

        self.assertRaises(SystemExit, check_uuid.run)
        with open(tests_file, "r") as f:
            self.assertTrue(TestCLInterface.CODE == f.read())

    def test_fix_argument_yes(self):
        temp_dir = tempfile.mkdtemp(prefix='check-uuid-yes', dir=".")
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        tests_file = self.create_tests_file(temp_dir)

        sys.argv = [sys.argv[0]] + ["--fix", "--package",
                                    os.path.relpath(temp_dir)]
        check_uuid.run()
        with open(tests_file, "r") as f:
            self.assertTrue(TestCLInterface.CODE != f.read())


class TestSourcePatcher(base.TestCase):
    def test_add_patch(self):
        patcher = check_uuid.SourcePatcher()
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        file_contents = 'first_line\nsecond_line'
        fake_file.write(file_contents)
        fake_file.close()
        patcher.add_patch(fake_file.name, 'patch', 2)

        source_file = patcher.source_files[fake_file.name]
        self.assertEqual(1, len(patcher.patches))
        (patch_id, patch), = patcher.patches.items()
        self.assertEqual(patcher._quote('patch\n'), patch)
        self.assertEqual('first_line\n{%s:s}second_line' % patch_id,
                         patcher._unquote(source_file))

    def test_apply_patches(self):
        fake_file = tempfile.NamedTemporaryFile("w+t")
        patcher = check_uuid.SourcePatcher()
        patcher.patches = {'fake-uuid': patcher._quote('patch\n')}
        patcher.source_files = {
            fake_file.name: patcher._quote('first_line\n') +
            '{fake-uuid:s}second_line'}
        with mock.patch('sys.stdout'):
            patcher.apply_patches()

        lines = fake_file.read().split('\n')
        fake_file.close()
        self.assertEqual(['first_line', 'patch', 'second_line'], lines)
        self.assertFalse(patcher.patches)
        self.assertFalse(patcher.source_files)


class TestTestChecker(base.TestCase):
    IMPORT_LINE = "from tempest.lib import decorators\n"

    def _test_add_uuid_to_test(self, source_file):
        class Fake_test_node():
            lineno = 1
            col_offset = 4
        patcher = check_uuid.SourcePatcher()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        fake_file.write(source_file)
        fake_file.close()
        checker._add_uuid_to_test(patcher, Fake_test_node(), fake_file.name)

        self.assertEqual(1, len(patcher.patches))
        self.assertEqual(1, len(patcher.source_files))
        (patch_id, patch), = patcher.patches.items()
        changed_source_file, = patcher.source_files.values()
        self.assertEqual('{%s:s}%s' % (patch_id, patcher._quote(source_file)),
                         changed_source_file)
        expected_patch_start = patcher._quote(
            '    ' + check_uuid.DECORATOR_TEMPLATE.split('(')[0])
        self.assertTrue(patch.startswith(expected_patch_start))

    def test_add_uuid_to_test_def(self):
        source_file = ("    def test_test():\n"
                       "        pass")
        self._test_add_uuid_to_test(source_file)

    def test_add_uuid_to_test_decorator(self):
        source_file = ("    @decorators.idempotent_id\n"
                       "    def test_test():\n"
                       "        pass")
        self._test_add_uuid_to_test(source_file)

    @staticmethod
    def get_mocked_ast_object(lineno, col_offset, module, name, object_type):
        ast_object = mock.Mock(spec=object_type)
        name_obj = mock.Mock()
        ast_object.lineno = lineno
        ast_object.col_offset = col_offset
        name_obj.name = name
        ast_object.module = module
        ast_object.names = [name_obj]

        return ast_object

    def test_add_import_for_test_uuid_no_tempest(self):
        patcher = check_uuid.SourcePatcher()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        source_code = "from unittest import mock\n"
        fake_file.write(source_code)
        fake_file.close()

        class Fake_src_parsed():
            body = [TestTestChecker.get_mocked_ast_object(
                1, 4, 'unittest', 'mock', ast.ImportFrom)]

        checker._add_import_for_test_uuid(patcher, Fake_src_parsed,
                                          fake_file.name)
        patcher.apply_patches()

        with open(fake_file.name, "r") as f:
            expected_result = source_code + '\n' + TestTestChecker.IMPORT_LINE
            self.assertTrue(expected_result == f.read())

    def test_add_import_for_test_uuid_tempest(self):
        patcher = check_uuid.SourcePatcher()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        source_code = "from tempest import a_fake_module\n"
        fake_file.write(source_code)
        fake_file.close()

        class Fake_src_parsed:
            body = [TestTestChecker.get_mocked_ast_object(
                1, 4, 'tempest', 'a_fake_module', ast.ImportFrom)]

        checker._add_import_for_test_uuid(patcher, Fake_src_parsed,
                                          fake_file.name)
        patcher.apply_patches()

        with open(fake_file.name, "r") as f:
            expected_result = source_code + TestTestChecker.IMPORT_LINE
            self.assertTrue(expected_result == f.read())

    def test_add_import_no_import(self):
        patcher = check_uuid.SourcePatcher()
        patcher.add_patch = mock.Mock()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        fake_file.close()

        class Fake_src_parsed:
            body = []

        checker._add_import_for_test_uuid(patcher, Fake_src_parsed,
                                          fake_file.name)

        self.assertTrue(not patcher.add_patch.called)
