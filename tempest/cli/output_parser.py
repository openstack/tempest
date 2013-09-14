# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

"""Collection of utilities for parsing CLI clients output."""

import re

from tempest.openstack.common import log as logging


LOG = logging.getLogger(__name__)


delimiter_line = re.compile('^\+\-[\+\-]+\-\+$')


def details_multiple(output_lines, with_label=False):
    """Return list of dicts with item details from cli output tables.

    If with_label is True, key '__label' is added to each items dict.
    For more about 'label' see OutputParser.tables().
    """
    items = []
    tables_ = tables(output_lines)
    for table_ in tables_:
        if 'Property' not in table_['headers'] \
           or 'Value' not in table_['headers']:
            raise Exception('Invalid structure of table with details')
        item = {}
        for value in table_['values']:
            item[value[0]] = value[1]
        if with_label:
            item['__label'] = table_['label']
        items.append(item)
    return items


def details(output_lines, with_label=False):
    """Return dict with details of first item (table) found in output."""
    items = details_multiple(output_lines, with_label)
    return items[0]


def listing(output_lines):
    """Return list of dicts with basic item info parsed from cli output.
    """

    items = []
    table_ = table(output_lines)
    for row in table_['values']:
        item = {}
        for col_idx, col_key in enumerate(table_['headers']):
            item[col_key] = row[col_idx]
        items.append(item)
    return items


def tables(output_lines):
    """Find all ascii-tables in output and parse them.

    Return list of tables parsed from cli output as dicts.
    (see OutputParser.table())

    And, if found, label key (separated line preceding the table)
    is added to each tables dict.
    """
    tables_ = []

    table_ = []
    label = None

    start = False
    header = False

    if not isinstance(output_lines, list):
        output_lines = output_lines.split('\n')

    for line in output_lines:
        if delimiter_line.match(line):
            if not start:
                start = True
            elif not header:
                # we are after head area
                header = True
            else:
                # table ends here
                start = header = None
                table_.append(line)

                parsed = table(table_)
                parsed['label'] = label
                tables_.append(parsed)

                table_ = []
                label = None
                continue
        if start:
            table_.append(line)
        else:
            if label is None:
                label = line
            else:
                LOG.warn('Invalid line between tables: %s' % line)
    if len(table_) > 0:
        LOG.warn('Missing end of table')

    return tables_


def table(output_lines):
    """Parse single table from cli output.

    Return dict with list of column names in 'headers' key and
    rows in 'values' key.
    """
    table_ = {'headers': [], 'values': []}
    columns = None

    if not isinstance(output_lines, list):
        output_lines = output_lines.split('\n')

    if not output_lines[-1]:
        # skip last line if empty (just newline at the end)
        output_lines = output_lines[:-1]

    for line in output_lines:
        if delimiter_line.match(line):
            columns = _table_columns(line)
            continue
        if '|' not in line:
            LOG.warn('skipping invalid table line: %s' % line)
            continue
        row = []
        for col in columns:
            row.append(line[col[0]:col[1]].strip())
        if table_['headers']:
            table_['values'].append(row)
        else:
            table_['headers'] = row

    return table_


def _table_columns(first_table_row):
    """Find column ranges in output line.

    Return list of tuples (start,end) for each column
    detected by plus (+) characters in delimiter line.
    """
    positions = []
    start = 1  # there is '+' at 0
    while start < len(first_table_row):
        end = first_table_row.find('+', start)
        if end == -1:
            break
        positions.append((start, end))
        start = end + 1
    return positions
