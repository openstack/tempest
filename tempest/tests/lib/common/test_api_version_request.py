# Copyright 2014 IBM Corp.
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

from tempest.lib.common import api_version_request
from tempest.lib import exceptions
from tempest.tests import base


class APIVersionRequestTests(base.TestCase):
    def test_valid_version_strings(self):
        def _test_string(version, exp_major, exp_minor):
            v = api_version_request.APIVersionRequest(version)
            self.assertEqual(v.ver_major, exp_major)
            self.assertEqual(v.ver_minor, exp_minor)

        _test_string("1.1", 1, 1)
        _test_string("2.10", 2, 10)
        _test_string("5.234", 5, 234)
        _test_string("12.5", 12, 5)
        _test_string("2.0", 2, 0)
        _test_string("2.200", 2, 200)

    def test_null_version(self):
        v = api_version_request.APIVersionRequest()
        self.assertTrue(v.is_null())

    def test_invalid_version_strings(self):
        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "2")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "200")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "2.1.4")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "200.23.66.3")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "5 .3")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "5. 3")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "5.03")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "02.1")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "2.001")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, " 2.1")

        self.assertRaises(exceptions.InvalidAPIVersionString,
                          api_version_request.APIVersionRequest, "2.1 ")

    def test_version_comparisons(self):
        vers2_0 = api_version_request.APIVersionRequest("2.0")
        vers2_5 = api_version_request.APIVersionRequest("2.5")
        vers5_23 = api_version_request.APIVersionRequest("5.23")
        v_null = api_version_request.APIVersionRequest()
        v_latest = api_version_request.APIVersionRequest('latest')

        self.assertTrue(v_null < vers2_5)
        self.assertTrue(vers2_0 < vers2_5)
        self.assertTrue(vers2_0 <= vers2_5)
        self.assertTrue(vers2_0 <= vers2_0)
        self.assertTrue(vers2_5 > v_null)
        self.assertTrue(vers5_23 > vers2_5)
        self.assertTrue(vers2_0 >= vers2_0)
        self.assertTrue(vers5_23 >= vers2_5)
        self.assertTrue(vers2_0 != vers2_5)
        self.assertTrue(vers2_0 == vers2_0)
        self.assertTrue(vers2_0 != v_null)
        self.assertTrue(v_null == v_null)
        self.assertTrue(vers2_0 <= v_latest)
        self.assertTrue(vers2_0 != v_latest)
        self.assertTrue(v_latest == v_latest)
        self.assertRaises(TypeError, vers2_0.__lt__, "2.1")

    def test_version_matches(self):
        vers2_0 = api_version_request.APIVersionRequest("2.0")
        vers2_5 = api_version_request.APIVersionRequest("2.5")
        vers2_45 = api_version_request.APIVersionRequest("2.45")
        vers3_3 = api_version_request.APIVersionRequest("3.3")
        vers3_23 = api_version_request.APIVersionRequest("3.23")
        vers4_0 = api_version_request.APIVersionRequest("4.0")
        v_null = api_version_request.APIVersionRequest()
        v_latest = api_version_request.APIVersionRequest('latest')

        def _check_version_matches(version, version1, version2, check=True):
            if check:
                msg = "Version %s does not matches with [%s - %s] range"
                self.assertTrue(version.matches(version1, version2),
                                msg % (version.get_string(),
                                       version1.get_string(),
                                       version2.get_string()))
            else:
                msg = "Version %s matches with [%s - %s] range"
                self.assertFalse(version.matches(version1, version2),
                                 msg % (version.get_string(),
                                        version1.get_string(),
                                        version2.get_string()))

        _check_version_matches(vers2_5, vers2_0, vers2_45)
        _check_version_matches(vers2_5, vers2_0, v_null)
        _check_version_matches(vers2_0, vers2_0, vers2_5)
        _check_version_matches(vers3_3, vers2_5, vers3_3)
        _check_version_matches(vers3_3, v_null, vers3_3)
        _check_version_matches(vers3_3, v_null, vers4_0)
        _check_version_matches(vers2_0, vers2_5, vers2_45, False)
        _check_version_matches(vers3_23, vers2_5, vers3_3, False)
        _check_version_matches(vers2_5, vers2_45, vers2_0, False)
        _check_version_matches(vers2_5, vers2_0, v_latest)
        _check_version_matches(v_latest, v_latest, v_latest)
        _check_version_matches(vers2_5, v_latest, v_latest, False)
        _check_version_matches(v_latest, vers2_0, vers4_0, False)

        self.assertRaises(ValueError, v_null.matches, vers2_0, vers2_45)

    def test_get_string(self):
        vers_string = ["3.23", "latest"]
        for ver in vers_string:
            ver_obj = api_version_request.APIVersionRequest(ver)
            self.assertEqual(ver, ver_obj.get_string())

        self.assertIsNotNone(
            api_version_request.APIVersionRequest().get_string)
