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

import importlib
import os
import sys
import tempfile
from unittest import mock

import fixtures

from tempest.lib.cmd import check_uuid
from tempest.tests import base


class TestCLInterface(base.TestCase):
    CODE = "import unittest\n" \
           "class TestClass(unittest.TestCase):\n" \
           "    def test_tests(self):\n" \
           "        pass"

    def create_tests_file(self, directory):
        with open(directory + "/__init__.py", "w"):
            pass

        tests_file = directory + "/tests.py"
        with open(tests_file, "w") as fake_file:
            fake_file.write(TestCLInterface.CODE)

        return tests_file

    def test_fix_argument_no(self):
        temp_dir = self.useFixture(fixtures.TempDir(rootdir="."))
        tests_file = self.create_tests_file(temp_dir.path)

        sys.argv = [sys.argv[0]] + ["--package",
                                    os.path.relpath(temp_dir.path)]

        self.assertRaises(SystemExit, check_uuid.run)
        with open(tests_file, "r") as f:
            self.assertTrue(TestCLInterface.CODE == f.read())

    def test_fix_argument_yes(self):
        temp_dir = self.useFixture(fixtures.TempDir(rootdir="."))
        tests_file = self.create_tests_file(temp_dir.path)

        sys.argv = [sys.argv[0]] + ["--fix", "--package",
                                    os.path.relpath(temp_dir.path)]

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

    def test_add_import_for_test_uuid_no_tempest(self):
        patcher = check_uuid.SourcePatcher()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t")

        class Fake_src_parsed():
            body = ['test_node']
        checker._import_name = mock.Mock(return_value='fake_module')

        checker._add_import_for_test_uuid(patcher, Fake_src_parsed(),
                                          fake_file.name)
        (patch_id, patch), = patcher.patches.items()
        self.assertEqual(patcher._quote('\n' + check_uuid.IMPORT_LINE + '\n'),
                         patch)
        self.assertEqual('{%s:s}' % patch_id,
                         patcher.source_files[fake_file.name])

    def test_add_import_for_test_uuid_tempest(self):
        patcher = check_uuid.SourcePatcher()
        checker = check_uuid.TestChecker(importlib.import_module('tempest'))
        fake_file = tempfile.NamedTemporaryFile("w+t", delete=False)
        test1 = ("    def test_test():\n"
                 "        pass\n")
        test2 = ("    def test_another_test():\n"
                 "        pass\n")
        source_code = test1 + test2
        fake_file.write(source_code)
        fake_file.close()

        def fake_import_name(node):
            return node.name
        checker._import_name = fake_import_name

        class Fake_node():
            def __init__(self, lineno, col_offset, name):
                self.lineno = lineno
                self.col_offset = col_offset
                self.name = name

        class Fake_src_parsed():
            body = [Fake_node(1, 4, 'tempest.a_fake_module'),
                    Fake_node(3, 4, 'another_fake_module')]

        checker._add_import_for_test_uuid(patcher, Fake_src_parsed(),
                                          fake_file.name)
        (patch_id, patch), = patcher.patches.items()
        self.assertEqual(patcher._quote(check_uuid.IMPORT_LINE + '\n'),
                         patch)
        expected_source = patcher._quote(test1) + '{' + patch_id + ':s}' +\
            patcher._quote(test2)
        self.assertEqual(expected_source,
                         patcher.source_files[fake_file.name])
