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

from unittest import mock

from tempest.common.utils import net_utils
from tempest.lib import exceptions as lib_exc
from tempest.tests import base


class TestGetPingPayloadSize(base.TestCase):

    def test_ipv4(self):
        self.assertEqual(1422, net_utils.get_ping_payload_size(1450, 4))

    def test_ipv6(self):
        self.assertEqual(1406, net_utils.get_ping_payload_size(1450, 6))

    def test_too_low_mtu(self):
        self.assertRaises(
            lib_exc.BadRequest, net_utils.get_ping_payload_size, 10, 4)

    def test_None(self):
        self.assertIsNone(net_utils.get_ping_payload_size(None, mock.Mock()))
