# Copyright 2020 Red Hat, Inc
# All Rights Reserved.
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

"""
Utility for content checking of a given dry_run.json file.
"""

import argparse
import json
import sys


def get_parser():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--is-empty', action="store_true", dest='is_empty',
                        default=False,
                        help="""Are values of a given dry_run.json empty?""")
    parser.add_argument('--file', dest='file', default=None, metavar='PATH',
                        help="A path to a dry_run.json file.")
    return parser


def parse_arguments():
    parser = get_parser()
    args = parser.parse_args()
    if not args.file:
        sys.stderr.write('Path to a dry_run.json must be specified.\n')
        sys.exit(1)
    return args


def load_json(path):
    """Load json content from file addressed by path."""
    try:
        with open(path, 'rb') as json_file:
            json_data = json.load(json_file)
    except Exception as ex:
        sys.exit(ex)
    return json_data


def are_values_empty(dry_run_content):
    """Return true if values of dry_run.json are empty."""
    for value in dry_run_content.values():
        if value:
            return False
    return True


def main():
    args = parse_arguments()
    content = load_json(args.file)
    if args.is_empty:
        if not are_values_empty(content):
            sys.exit(1)


if __name__ == "__main__":
    main()
