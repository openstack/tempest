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

import netaddr

from tempest.lib.common.utils import data_utils
from tempest.tests import base


class TestDataUtils(base.TestCase):

    def test_rand_uuid(self):
        actual = data_utils.rand_uuid()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]"
                         "{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
        actual2 = data_utils.rand_uuid()
        self.assertNotEqual(actual, actual2)

    def test_rand_uuid_hex(self):
        actual = data_utils.rand_uuid_hex()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^[0-9a-f]{32}$")

        actual2 = data_utils.rand_uuid_hex()
        self.assertNotEqual(actual, actual2)

    def test_rand_name(self):
        actual = data_utils.rand_name()
        self.assertIsInstance(actual, str)
        actual2 = data_utils.rand_name()
        self.assertNotEqual(actual, actual2)

        actual = data_utils.rand_name('foo')
        self.assertTrue(actual.startswith('foo'))
        actual2 = data_utils.rand_name('foo')
        self.assertTrue(actual.startswith('foo'))
        self.assertNotEqual(actual, actual2)

    def test_rand_name_with_prefix(self):
        actual = data_utils.rand_name(prefix='prefix-str')
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^prefix-str-")
        actual2 = data_utils.rand_name(prefix='prefix-str')
        self.assertNotEqual(actual, actual2)

    def test_rand_password(self):
        actual = data_utils.rand_password()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "[A-Za-z0-9~!@#$%^&*_=+]{15,}")
        actual2 = data_utils.rand_password()
        self.assertNotEqual(actual, actual2)

    def test_rand_password_with_len(self):
        actual = data_utils.rand_password(8)
        self.assertIsInstance(actual, str)
        self.assertEqual(len(actual), 8)
        self.assertRegex(actual, "[A-Za-z0-9~!@#$%^&*_=+]{8}")
        actual2 = data_utils.rand_password(8)
        self.assertNotEqual(actual, actual2)

    def test_rand_password_with_len_2(self):
        actual = data_utils.rand_password(2)
        self.assertIsInstance(actual, str)
        self.assertEqual(len(actual), 3)
        self.assertRegex(actual, "[A-Za-z0-9~!@#$%^&*_=+]{3}")
        actual2 = data_utils.rand_password(2)
        self.assertNotEqual(actual, actual2)

    def test_rand_url(self):
        actual = data_utils.rand_url()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^https://url-[0-9]*\.com$")
        actual2 = data_utils.rand_url()
        self.assertNotEqual(actual, actual2)

    def test_rand_int(self):
        actual = data_utils.rand_int_id()
        self.assertIsInstance(actual, int)

        actual2 = data_utils.rand_int_id()
        self.assertNotEqual(actual, actual2)

    def test_rand_infiniband_guid_address(self):
        actual = data_utils.rand_infiniband_guid_address()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^([0-9a-f][0-9a-f]:){7}"
                         "[0-9a-f][0-9a-f]$")

        actual2 = data_utils.rand_infiniband_guid_address()
        self.assertNotEqual(actual, actual2)

    def test_rand_mac_address(self):
        actual = data_utils.rand_mac_address()
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^([0-9a-f][0-9a-f]:){5}"
                         "[0-9a-f][0-9a-f]$")

        actual2 = data_utils.rand_mac_address()
        self.assertNotEqual(actual, actual2)

    def test_parse_image_id(self):
        actual = data_utils.parse_image_id("/foo/bar/deadbeaf")
        self.assertEqual("deadbeaf", actual)

    def test_arbitrary_string(self):
        actual = data_utils.arbitrary_string()
        self.assertEqual(actual, "test")
        actual = data_utils.arbitrary_string(size=30, base_text="abc")
        self.assertEqual(actual, "abc" * int(30 / len("abc")))
        actual = data_utils.arbitrary_string(size=5, base_text="deadbeaf")
        self.assertEqual(actual, "deadb")

    def test_random_bytes(self):
        actual = data_utils.random_bytes()  # default size=1024
        self.assertIsInstance(actual, str)
        self.assertRegex(actual, "^[\x00-\xFF]{1024}")
        actual2 = data_utils.random_bytes()
        self.assertNotEqual(actual, actual2)

        actual = data_utils.random_bytes(size=2048)
        self.assertRegex(actual, "^[\x00-\xFF]{2048}")

    def test_get_ipv6_addr_by_EUI64(self):
        actual = data_utils.get_ipv6_addr_by_EUI64('2001:db8::',
                                                   '00:16:3e:33:44:55')
        self.assertIsInstance(actual, netaddr.IPAddress)
        self.assertEqual(actual,
                         netaddr.IPAddress('2001:db8::216:3eff:fe33:4455'))

    def test_get_ipv6_addr_by_EUI64_with_IPv4_prefix(self):
        ipv4_prefix = '10.0.8'
        mac = '00:16:3e:33:44:55'
        self.assertRaises(TypeError, data_utils.get_ipv6_addr_by_EUI64,
                          ipv4_prefix, mac)

    def test_get_ipv6_addr_by_EUI64_bad_cidr_type(self):
        bad_cidr = 123
        mac = '00:16:3e:33:44:55'
        self.assertRaises(TypeError, data_utils.get_ipv6_addr_by_EUI64,
                          bad_cidr, mac)

    def test_get_ipv6_addr_by_EUI64_bad_cidr_value(self):
        bad_cidr = 'bb'
        mac = '00:16:3e:33:44:55'
        self.assertRaises(TypeError, data_utils.get_ipv6_addr_by_EUI64,
                          bad_cidr, mac)

    def test_get_ipv6_addr_by_EUI64_bad_mac_value(self):
        cidr = '2001:db8::'
        bad_mac = '00:16:3e:33:44:5Z'
        self.assertRaises(TypeError, data_utils.get_ipv6_addr_by_EUI64,
                          cidr, bad_mac)

    def test_get_ipv6_addr_by_EUI64_bad_mac_type(self):
        cidr = '2001:db8::'
        bad_mac = 99999999999999999999
        self.assertRaises(TypeError, data_utils.get_ipv6_addr_by_EUI64,
                          cidr, bad_mac)
