# Copyright 2014 Matthew Treinish
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

from tempest.hacking import checks
from tempest.tests import base


class HackingTestCase(base.TestCase):
    """
    This class tests the hacking checks in tempest.hacking.checks by passing
    strings to the check methods like the pep8/flake8 parser would. The parser
    loops over each line in the file and then passes the parameters to the
    check method. The parameter names in the check method dictate what type of
    object is passed to the check method. The parameter types are::

        logical_line: A processed line with the following modifications:
            - Multi-line statements converted to a single line.
            - Stripped left and right.
            - Contents of strings replaced with "xxx" of same length.
            - Comments removed.
        physical_line: Raw line of text from the input file.
        lines: a list of the raw lines from the input file
        tokens: the tokens that contribute to this logical line
        line_number: line number in the input file
        total_lines: number of lines in the input file
        blank_lines: blank lines before this one
        indent_char: indentation character in this file (" " or "\t")
        indent_level: indentation (with tabs expanded to multiples of 8)
        previous_indent_level: indentation on previous line
        previous_logical: previous logical line
        filename: Path of the file being run through pep8

    When running a test on a check method the return will be False/None if
    there is no violation in the sample input. If there is an error a tuple is
    returned with a position in the line, and a message. So to check the result
    just assertTrue if the check is expected to fail and assertFalse if it
    should pass.
    """
    def test_no_setup_teardown_class_for_tests(self):
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def setUpClass(cls):", './tempest/tests/fake_test.py'))
        self.assertIsNone(checks.no_setup_teardown_class_for_tests(
            "  def setUpClass(cls): # noqa", './tempest/tests/fake_test.py'))
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def setUpClass(cls):", './tempest/api/fake_test.py'))
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def setUpClass(cls):", './tempest/scenario/fake_test.py'))
        self.assertFalse(checks.no_setup_teardown_class_for_tests(
            "  def setUpClass(cls):", './tempest/test.py'))
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def tearDownClass(cls):", './tempest/tests/fake_test.py'))
        self.assertIsNone(checks.no_setup_teardown_class_for_tests(
            "  def tearDownClass(cls): # noqa", './tempest/tests/fake_test.py'))
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def tearDownClass(cls):", './tempest/api/fake_test.py'))
        self.assertTrue(checks.no_setup_teardown_class_for_tests(
            "  def tearDownClass(cls):", './tempest/scenario/fake_test.py'))
        self.assertFalse(checks.no_setup_teardown_class_for_tests(
            "  def tearDownClass(cls):", './tempest/test.py'))

    def test_import_no_clients_in_api_and_scenario_tests(self):
        for client in checks.PYTHON_CLIENTS:
            string = "import " + client + "client"
            self.assertTrue(
                checks.import_no_clients_in_api_and_scenario_tests(
                    string, './tempest/api/fake_test.py'))
            self.assertTrue(
                checks.import_no_clients_in_api_and_scenario_tests(
                    string, './tempest/scenario/fake_test.py'))
            self.assertFalse(
                checks.import_no_clients_in_api_and_scenario_tests(
                    string, './tempest/test.py'))

    def test_scenario_tests_need_service_tags(self):
        self.assertFalse(checks.scenario_tests_need_service_tags(
            'def test_fake:', './tempest/scenario/test_fake.py',
            "@test.services('compute')"))
        self.assertFalse(checks.scenario_tests_need_service_tags(
            'def test_fake_test:', './tempest/api/compute/test_fake.py',
            "@test.services('image')"))
        self.assertFalse(checks.scenario_tests_need_service_tags(
            'def test_fake:', './tempest/scenario/orchestration/test_fake.py',
            "@test.services('compute')"))
        self.assertTrue(checks.scenario_tests_need_service_tags(
            'def test_fake_test:', './tempest/scenario/test_fake.py',
            '\n'))
        self.assertTrue(checks.scenario_tests_need_service_tags(
            'def test_fake:', './tempest/scenario/orchestration/test_fake.py',
            "\n"))

    def test_no_vi_headers(self):
        # NOTE(mtreinish)  The lines parameter is used only for finding the
        # line location in the file. So these tests just pass a list of an
        # arbitrary length to use for verifying the check function.
        self.assertTrue(checks.no_vi_headers(
            '# vim: tabstop=4 shiftwidth=4 softtabstop=4', 1, range(250)))
        self.assertTrue(checks.no_vi_headers(
            '# vim: tabstop=4 shiftwidth=4 softtabstop=4', 249, range(250)))
        self.assertFalse(checks.no_vi_headers(
            '# vim: tabstop=4 shiftwidth=4 softtabstop=4', 149, range(250)))

    def test_service_tags_not_in_module_path(self):
        self.assertTrue(checks.service_tags_not_in_module_path(
            "@test.services('compute')", './tempest/api/compute/fake_test.py'))
        self.assertFalse(checks.service_tags_not_in_module_path(
            "@test.services('compute')",
            './tempest/scenario/compute/fake_test.py'))
        self.assertFalse(checks.service_tags_not_in_module_path(
            "@test.services('compute')", './tempest/api/image/fake_test.py'))

    def test_no_mutable_default_args(self):
        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            " def function1(para={}):"))))

        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            "def function2(para1, para2, para3=[])"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined = []"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined, undefined = [], {}"))))
