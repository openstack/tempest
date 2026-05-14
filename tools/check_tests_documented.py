#!/usr/bin/env python3

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Check that all test modules have a corresponding automodule RST entry."""

import importlib
import os
import pkgutil
import sys

PACKAGES = (
    'tempest.api',
    'tempest.scenario',
    'tempest.serial_tests',
)
RST_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'doc', 'source', 'tests'
)


def get_python_modules():
    modules = set()
    for package_name in PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except ImportError as exc:
            print(
                f'ERROR: Could not import {package_name}: {exc}',
                file=sys.stderr,
            )
            sys.exit(1)
        for _, modname, _ in pkgutil.walk_packages(
            path=package.__path__,
            prefix=package.__name__ + '.',
        ):
            modules.add(modname)
    return modules


def get_documented_modules():
    documented = set()
    for root, _dirs, files in os.walk(RST_DIR):
        for filename in files:
            if not filename.endswith('.rst'):
                continue
            with open(os.path.join(root, filename)) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('.. automodule::'):
                        documented.add(line.split('::', 1)[1].strip())
    return documented


def main():
    python_modules = get_python_modules()
    documented_modules = get_documented_modules()

    missing = python_modules - documented_modules

    if missing:
        print('The following test modules lack an automodule RST entry:')
        for mod in sorted(missing):
            print(f'  {mod}')
        return 1

    print(f'All {len(python_modules)} test modules are documented.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
