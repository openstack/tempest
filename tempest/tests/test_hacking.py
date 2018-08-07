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
    """Test class for hacking rule

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
            "@utils.services('compute')"))
        self.assertFalse(checks.scenario_tests_need_service_tags(
            'def test_fake_test:', './tempest/api/compute/test_fake.py',
            "@utils.services('image')"))
        self.assertFalse(checks.scenario_tests_need_service_tags(
            'def test_fake:', './tempest/scenario/orchestration/test_fake.py',
            "@utils.services('compute')"))
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
            "@utils.services('compute')",
            './tempest/api/compute/fake_test.py'))
        self.assertFalse(checks.service_tags_not_in_module_path(
            "@utils.services('compute')",
            './tempest/scenario/compute/fake_test.py'))
        self.assertFalse(checks.service_tags_not_in_module_path(
            "@utils.services('compute')", './tempest/api/image/fake_test.py'))

    def test_no_hyphen_at_end_of_rand_name(self):
        self.assertIsNone(checks.no_hyphen_at_end_of_rand_name(
            'data_utils.rand_name("fake-resource")', './tempest/test_foo.py'))
        self.assertEqual(2, len(list(checks.no_hyphen_at_end_of_rand_name(
            'data_utils.rand_name("fake-resource-")', './tempest/test_foo.py')
        )))

    def test_no_mutable_default_args(self):
        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            " def function1(para={}):"))))

        self.assertEqual(1, len(list(checks.no_mutable_default_args(
            "def function2(para1, para2, para3=[])"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined = []"))))

        self.assertEqual(0, len(list(checks.no_mutable_default_args(
            "defined, undefined = [], {}"))))

    def test_no_testtools_skip_decorator(self):
        self.assertEqual(1, len(list(checks.no_testtools_skip_decorator(
            " @testtools.skip('Bug xxx')"))))
        self.assertEqual(0, len(list(checks.no_testtools_skip_decorator(
            " @testtools.skipUnless(CONF.something, 'msg')"))))
        self.assertEqual(0, len(list(checks.no_testtools_skip_decorator(
            " @testtools.skipIf(CONF.something, 'msg')"))))

    def test_dont_import_local_tempest_code_into_lib(self):
        self.assertEqual(0, len(list(checks.dont_import_local_tempest_into_lib(
            "from tempest.common import waiters",
            './tempest/common/compute.py'))))
        self.assertEqual(0, len(list(checks.dont_import_local_tempest_into_lib(
            "from tempest import config",
            './tempest/common/compute.py'))))
        self.assertEqual(0, len(list(checks.dont_import_local_tempest_into_lib(
            "import tempest.exception",
            './tempest/common/compute.py'))))
        self.assertEqual(1, len(list(checks.dont_import_local_tempest_into_lib(
            "from tempest.common import waiters",
            './tempest/lib/common/compute.py'))))
        self.assertEqual(1, len(list(checks.dont_import_local_tempest_into_lib(
            "from tempest import config",
            './tempest/lib/common/compute.py'))))
        self.assertEqual(1, len(list(checks.dont_import_local_tempest_into_lib(
            "import tempest.exception",
            './tempest/lib/common/compute.py'))))

    def test_dont_use_config_in_tempest_lib(self):
        self.assertFalse(list(checks.dont_use_config_in_tempest_lib(
            'from tempest import config', './tempest/common/compute.py')))
        self.assertFalse(list(checks.dont_use_config_in_tempest_lib(
            'from oslo_concurrency import lockutils',
            './tempest/lib/auth.py')))
        self.assertTrue(list(checks.dont_use_config_in_tempest_lib(
            'from tempest import config', './tempest/lib/auth.py')))
        self.assertTrue(list(checks.dont_use_config_in_tempest_lib(
            'from oslo_config import cfg', './tempest/lib/decorators.py')))
        self.assertTrue(list(checks.dont_use_config_in_tempest_lib(
            'import tempest.config', './tempest/lib/common/rest_client.py')))

    def test_unsupported_exception_attribute_PY3(self):
        self.assertEqual(len(list(checks.unsupported_exception_attribute_PY3(
            "raise TestCase.failureException(e.message)"))), 1)
        self.assertEqual(len(list(checks.unsupported_exception_attribute_PY3(
            "raise TestCase.failureException(ex.message)"))), 1)
        self.assertEqual(len(list(checks.unsupported_exception_attribute_PY3(
            "raise TestCase.failureException(exc.message)"))), 1)
        self.assertEqual(len(list(checks.unsupported_exception_attribute_PY3(
            "raise TestCase.failureException(exception.message)"))), 1)
        self.assertEqual(len(list(checks.unsupported_exception_attribute_PY3(
            "raise TestCase.failureException(ee.message)"))), 0)

    def _test_no_negatve_test_attribute_applied_to_negative_test(
            self, filename, with_other_decorators=False,
            with_negative_decorator=True, expected_success=True):
        check = checks.negative_test_attribute_always_applied_to_negative_tests
        other_decorators = [
            "@decorators.idempotent_id(123)",
            "@utils.requires_ext(extension='ext', service='svc')"
        ]

        if with_other_decorators:
            # Include multiple decorators to verify that this check works with
            # arbitrarily many decorators. These insert decorators above the
            # @decorators.attr(type=['negative']) decorator.
            for decorator in other_decorators:
                self.assertIsNone(check(" %s" % decorator, filename))
        if with_negative_decorator:
            self.assertIsNone(
                check("@decorators.attr(type=['negative'])", filename))
        if with_other_decorators:
            # Include multiple decorators to verify that this check works with
            # arbitrarily many decorators. These insert decorators between
            # the test and the @decorators.attr(type=['negative']) decorator.
            for decorator in other_decorators:
                self.assertIsNone(check(" %s" % decorator, filename))
        final_result = check(" def test_some_negative_case", filename)
        if expected_success:
            self.assertIsNone(final_result)
        else:
            self.assertIsInstance(final_result, tuple)
            self.assertFalse(final_result[0])

    def test_no_negatve_test_attribute_applied_to_negative_test(self):
        # Check negative filename, negative decorator passes
        self._test_no_negatve_test_attribute_applied_to_negative_test(
            "./tempest/api/test_something_negative.py")
        # Check negative filename, negative decorator, other decorators passes
        self._test_no_negatve_test_attribute_applied_to_negative_test(
            "./tempest/api/test_something_negative.py",
            with_other_decorators=True)

        # Check non-negative filename skips check, causing pass
        self._test_no_negatve_test_attribute_applied_to_negative_test(
            "./tempest/api/test_something.py")

        # Check negative filename, no negative decorator fails
        self._test_no_negatve_test_attribute_applied_to_negative_test(
            "./tempest/api/test_something_negative.py",
            with_negative_decorator=False,
            expected_success=False)
        # Check negative filename, no negative decorator, other decorators
        # fails
        self._test_no_negatve_test_attribute_applied_to_negative_test(
            "./tempest/api/test_something_negative.py",
            with_other_decorators=True,
            with_negative_decorator=False,
            expected_success=False)
