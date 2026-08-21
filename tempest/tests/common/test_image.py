# Copyright 2026 Red Hat, Inc.
# All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import http.client
import ipaddress
from urllib.parse import urlparse

from tempest.common import image
from tempest.tests import base


class TestRandomDataServer(base.TestCase):
    def test_binds_non_loopback_host(self):
        server = image.RandomDataServer()
        server.start()
        self.addCleanup(server.stop)

        addr = ipaddress.ip_address(server.host)
        self.assertFalse(addr.is_loopback)
        self.assertFalse(addr.is_link_local)
        self.assertNotIn('localhost', server.url)

        parsed = urlparse(server.url)
        conn = http.client.HTTPConnection(
            parsed.hostname, parsed.port, timeout=5)
        try:
            conn.request('HEAD', '/')
            self.assertEqual(200, conn.getresponse().status)
        finally:
            conn.close()
