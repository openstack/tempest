# Copyright 2015 NEC Corporation.  All rights reserved.
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

import testtools

from tempest.lib.common import api_version_utils
from tempest.lib import exceptions
from tempest.tests import base


class TestVersionSkipLogic(base.TestCase):

    def _test_version(self, test_min_version, test_max_version,
                      cfg_min_version, cfg_max_version, expected_skip=False):
        try:
            api_version_utils.check_skip_with_microversion(test_min_version,
                                                           test_max_version,
                                                           cfg_min_version,
                                                           cfg_max_version)
        except testtools.TestCase.skipException as e:
            if not expected_skip:
                raise testtools.TestCase.failureException(e.message)

    def test_version_min_in_range(self):
        self._test_version('2.2', '2.10', '2.1', '2.7')

    def test_version_max_in_range(self):
        self._test_version('2.1', '2.3', '2.2', '2.7')

    def test_version_cfg_in_range(self):
        self._test_version('2.2', '2.9', '2.3', '2.7')

    def test_version_equal(self):
        self._test_version('2.2', '2.2', '2.2', '2.2')

    def test_version_below_cfg_min(self):
        self._test_version('2.2', '2.4', '2.5', '2.7', expected_skip=True)

    def test_version_above_cfg_max(self):
        self._test_version('2.8', '2.9', '2.3', '2.7', expected_skip=True)

    def test_version_min_greater_than_max(self):
        self.assertRaises(exceptions.InvalidAPIVersionRange,
                          self._test_version, '2.8', '2.7', '2.3', '2.7')

    def test_cfg_version_min_greater_than_max(self):
        self.assertRaises(exceptions.InvalidAPIVersionRange,
                          self._test_version, '2.2', '2.7', '2.9', '2.7')


class TestSelectRequestMicroversion(base.TestCase):

    def _test_request_version(self, test_min_version,
                              cfg_min_version, expected_version):
        selected_version = api_version_utils.select_request_microversion(
            test_min_version, cfg_min_version)
        self.assertEqual(expected_version, selected_version)

    def test_cfg_min_version_greater(self):
        self._test_request_version('2.1', '2.3', expected_version='2.3')

    def test_class_min_version_greater(self):
        self._test_request_version('2.5', '2.3', expected_version='2.5')

    def test_cfg_min_version_none(self):
        self._test_request_version('2.5', None, expected_version='2.5')

    def test_class_min_version_none(self):
        self._test_request_version(None, '2.3', expected_version='2.3')

    def test_both_min_version_none(self):
        self._test_request_version(None, None, expected_version=None)

    def test_both_min_version_equal(self):
        self._test_request_version('2.3', '2.3', expected_version='2.3')


class TestMicroversionHeaderMatches(base.TestCase):

    def test_header_matches(self):
        microversion_header_name = 'x-openstack-xyz-api-version'
        request_microversion = '2.1'
        test_respose = {microversion_header_name: request_microversion}
        api_version_utils.assert_version_header_matches_request(
            microversion_header_name, request_microversion, test_respose)

    def test_header_does_not_match(self):
        microversion_header_name = 'x-openstack-xyz-api-version'
        request_microversion = '2.1'
        test_respose = {microversion_header_name: '2.2'}
        self.assertRaises(
            exceptions.InvalidHTTPResponseHeader,
            api_version_utils.assert_version_header_matches_request,
            microversion_header_name, request_microversion, test_respose)

    def test_header_not_present(self):
        microversion_header_name = 'x-openstack-xyz-api-version'
        request_microversion = '2.1'
        test_respose = {}
        self.assertRaises(
            exceptions.InvalidHTTPResponseHeader,
            api_version_utils.assert_version_header_matches_request,
            microversion_header_name, request_microversion, test_respose)
