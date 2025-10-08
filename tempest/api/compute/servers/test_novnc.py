# Copyright 2016-2017 OpenStack Foundation
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

import urllib.parse as urlparse

from tempest.api.compute import base
from tempest.common import compute
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class NoVNCConsoleTestJSON(base.BaseV2ComputeTest,
                           compute.NoVNCValidateMixin):
    """Test novnc console"""

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(NoVNCConsoleTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.vnc_console:
            raise cls.skipException('VNC Console feature is disabled.')

    def setUp(self):
        super(NoVNCConsoleTestJSON, self).setUp()
        self.websocket = None

    def tearDown(self):
        super(NoVNCConsoleTestJSON, self).tearDown()
        if self.websocket is not None:
            self.websocket.close()
        # NOTE(zhufl): Because server_check_teardown will raise Exception
        # which will prevent other cleanup steps from being executed, so
        # server_check_teardown should be called after super's tearDown.
        self.server_check_teardown()

    @classmethod
    def setup_clients(cls):
        super(NoVNCConsoleTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(NoVNCConsoleTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until="ACTIVE")
        cls.use_get_remote_console = False
        if not cls.is_requested_microversion_compatible('2.5'):
            cls.use_get_remote_console = True

    @decorators.idempotent_id('c640fdff-8ab4-45a4-a5d8-7e6146cbd0dc')
    def test_novnc(self):
        """Test accessing novnc console of server"""
        if self.use_get_remote_console:
            body = self.client.get_remote_console(
                self.server['id'], console_type='novnc',
                protocol='vnc')['remote_console']
        else:
            body = self.client.get_vnc_console(self.server['id'],
                                               type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the initial HTTP Request to novncproxy to get the NoVNC JavaScript
        self.validate_novnc_html(body['url'])
        # Do the WebSockify HTTP Request to novncproxy to do the RFB connection
        self.websocket = compute.create_websocket(body['url'])
        # Validate that we successfully connected and upgraded to Web Sockets
        self.validate_websocket_upgrade()
        # Validate the RFB Negotiation to determine if a valid VNC session
        self.validate_rfb_negotiation()

    @decorators.idempotent_id('f9c79937-addc-4aaa-9e0e-841eef02aeb7')
    def test_novnc_bad_token(self):
        """Test accessing novnc console with bad token

        Do the WebSockify HTTP Request to novnc proxy with a bad token,
        the novnc proxy should reject the connection and closed it.
        """
        if self.use_get_remote_console:
            body = self.client.get_remote_console(
                self.server['id'], console_type='novnc',
                protocol='vnc')['remote_console']
        else:
            body = self.client.get_vnc_console(self.server['id'],
                                               type='novnc')['console']
        self.assertEqual('novnc', body['type'])
        # Do the WebSockify HTTP Request to novncproxy with a bad token
        parts = urlparse.urlparse(body['url'])
        qparams = urlparse.parse_qs(parts.query)
        if 'path' in qparams:
            qparams['path'] = urlparse.unquote(qparams['path'][0]).replace(
                'token=', 'token=bad')
        elif 'token' in qparams:
            qparams['token'] = 'bad' + qparams['token'][0]
        new_query = urlparse.urlencode(qparams)
        new_parts = urlparse.ParseResult(parts.scheme, parts.netloc,
                                         parts.path, parts.params, new_query,
                                         parts.fragment)
        url = urlparse.urlunparse(new_parts)
        self.websocket = compute.create_websocket(url)
        # Make sure the novncproxy rejected the connection and closed it
        data = self.websocket.receive_frame()
        self.assertTrue(data is None or not data,
                        "The novnc proxy actually sent us some data, but we "
                        "expected it to close the connection.")
