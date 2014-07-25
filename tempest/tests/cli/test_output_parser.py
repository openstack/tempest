# Copyright 2014 NEC Corporation.
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


from tempest.cli import output_parser
from tempest import exceptions
from tempest.tests import base


class TestOutputParser(base.TestCase):
    OUTPUT_LINES = """
+----+------+---------+
| ID | Name | Status  |
+----+------+---------+
| 11 | foo  | BUILD   |
| 21 | bar  | ERROR   |
| 31 | bee  | None    |
+----+------+---------+
"""
    OUTPUT_LINES2 = """
+----+-------+---------+
| ID | Name2 | Status2 |
+----+-------+---------+
| 41 | aaa   | SSSSS   |
| 51 | bbb   | TTTTT   |
| 61 | ccc   | AAAAA   |
+----+-------+---------+
"""

    EXPECTED_TABLE = {'headers': ['ID', 'Name', 'Status'],
                      'values': [['11', 'foo', 'BUILD'],
                                 ['21', 'bar', 'ERROR'],
                                 ['31', 'bee', 'None']]}
    EXPECTED_TABLE2 = {'headers': ['ID', 'Name2', 'Status2'],
                       'values': [['41', 'aaa', 'SSSSS'],
                                  ['51', 'bbb', 'TTTTT'],
                                  ['61', 'ccc', 'AAAAA']]}

    def test_table_with_normal_values(self):
        actual = output_parser.table(self.OUTPUT_LINES)
        self.assertIsInstance(actual, dict)
        self.assertEqual(self.EXPECTED_TABLE, actual)

    def test_table_with_list(self):
        output_lines = self.OUTPUT_LINES.split('\n')
        actual = output_parser.table(output_lines)
        self.assertIsInstance(actual, dict)
        self.assertEqual(self.EXPECTED_TABLE, actual)

    def test_table_with_invalid_line(self):
        output_lines = self.OUTPUT_LINES + "aaaa"
        actual = output_parser.table(output_lines)
        self.assertIsInstance(actual, dict)
        self.assertEqual(self.EXPECTED_TABLE, actual)

    def test_tables_with_normal_values(self):
        output_lines = 'test' + self.OUTPUT_LINES +\
                       'test2' + self.OUTPUT_LINES2
        expected = [{'headers': self.EXPECTED_TABLE['headers'],
                     'label': 'test',
                     'values': self.EXPECTED_TABLE['values']},
                    {'headers': self.EXPECTED_TABLE2['headers'],
                     'label': 'test2',
                     'values': self.EXPECTED_TABLE2['values']}]
        actual = output_parser.tables(output_lines)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)

    def test_tables_with_invalid_values(self):
        output_lines = 'test' + self.OUTPUT_LINES +\
                       'test2' + self.OUTPUT_LINES2 + '\n'
        expected = [{'headers': self.EXPECTED_TABLE['headers'],
                     'label': 'test',
                     'values': self.EXPECTED_TABLE['values']},
                    {'headers': self.EXPECTED_TABLE2['headers'],
                     'label': 'test2',
                     'values': self.EXPECTED_TABLE2['values']}]
        actual = output_parser.tables(output_lines)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)

    def test_tables_with_invalid_line(self):
        output_lines = 'test' + self.OUTPUT_LINES +\
                       'test2' + self.OUTPUT_LINES2 +\
                       '+----+-------+---------+'
        expected = [{'headers': self.EXPECTED_TABLE['headers'],
                     'label': 'test',
                     'values': self.EXPECTED_TABLE['values']},
                    {'headers': self.EXPECTED_TABLE2['headers'],
                     'label': 'test2',
                     'values': self.EXPECTED_TABLE2['values']}]

        actual = output_parser.tables(output_lines)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)

    LISTING_OUTPUT = """
+----+
| ID |
+----+
| 11 |
| 21 |
| 31 |
+----+
"""

    def test_listing(self):
        expected = [{'ID': '11'}, {'ID': '21'}, {'ID': '31'}]
        actual = output_parser.listing(self.LISTING_OUTPUT)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)

    def test_details_multiple_with_invalid_line(self):
        self.assertRaises(exceptions.InvalidStructure,
                          output_parser.details_multiple,
                          self.OUTPUT_LINES)

    DETAILS_LINES1 = """First Table
+----------+--------+
| Property | Value  |
+----------+--------+
| foo      | BUILD  |
| bar      | ERROR  |
| bee      | None   |
+----------+--------+
"""
    DETAILS_LINES2 = """Second Table
+----------+--------+
| Property | Value  |
+----------+--------+
| aaa      | VVVVV  |
| bbb      | WWWWW  |
| ccc      | XXXXX  |
+----------+--------+
"""

    def test_details_with_normal_line_label_false(self):
        expected = {'foo': 'BUILD', 'bar': 'ERROR', 'bee': 'None'}
        actual = output_parser.details(self.DETAILS_LINES1)
        self.assertEqual(expected, actual)

    def test_details_with_normal_line_label_true(self):
        expected = {'__label': 'First Table',
                    'foo': 'BUILD', 'bar': 'ERROR', 'bee': 'None'}
        actual = output_parser.details(self.DETAILS_LINES1, with_label=True)
        self.assertEqual(expected, actual)

    def test_details_multiple_with_normal_line_label_false(self):
        expected = [{'foo': 'BUILD', 'bar': 'ERROR', 'bee': 'None'},
                    {'aaa': 'VVVVV', 'bbb': 'WWWWW', 'ccc': 'XXXXX'}]
        actual = output_parser.details_multiple(self.DETAILS_LINES1 +
                                                self.DETAILS_LINES2)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)

    def test_details_multiple_with_normal_line_label_true(self):
        expected = [{'__label': 'First Table',
                     'foo': 'BUILD', 'bar': 'ERROR', 'bee': 'None'},
                    {'__label': 'Second Table',
                     'aaa': 'VVVVV', 'bbb': 'WWWWW', 'ccc': 'XXXXX'}]
        actual = output_parser.details_multiple(self.DETAILS_LINES1 +
                                                self.DETAILS_LINES2,
                                                with_label=True)
        self.assertIsInstance(actual, list)
        self.assertEqual(expected, actual)
