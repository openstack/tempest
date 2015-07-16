# Copyright 2013 IBM Corp.
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

import os
import sys

from tempest.test_discover import plugins

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest


def load_tests(loader, tests, pattern):
    ext_plugins = plugins.TempestTestPluginManager()

    suite = unittest.TestSuite()
    base_path = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
    base_path = os.path.split(base_path)[0]
    # Load local tempest tests
    for test_dir in ['tempest/api', 'tempest/scenario',
                     'tempest/thirdparty']:
        full_test_dir = os.path.join(base_path, test_dir)
        if not pattern:
            suite.addTests(loader.discover(full_test_dir,
                                           top_level_dir=base_path))
        else:
            suite.addTests(loader.discover(full_test_dir, pattern=pattern,
                           top_level_dir=base_path))

    plugin_load_tests = ext_plugins.get_plugin_load_tests_tuple()
    if not plugin_load_tests:
        return suite

    # Load any installed plugin tests
    for plugin in plugin_load_tests:
        test_dir, top_path = plugin_load_tests[plugin]
        if not pattern:
            suite.addTests(loader.discover(test_dir, top_level_dir=top_path))
        else:
            suite.addTests(loader.discover(test_dir, pattern=pattern,
                                           top_level_dir=top_path))
    return suite
