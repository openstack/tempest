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

import socket
import struct
import urllib.parse as urlparse

from tempest.api.compute import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class SpiceDirectConsoleTestJSON(base.BaseV2ComputeAdminTest):
    """Test the spice-direct console"""

    create_default_network = True

    min_microversion = '2.99'
    max_microversion = 'latest'

    # SPICE client protocol constants
    magic = b'REDQ'
    major = 2
    minor = 2
    main_channel = 1
    common_caps = 11  # AuthSelection, AuthSpice, MiniHeader
    channel_caps = 9  # SemiSeamlessMigrate, SeamlessMigrate

    @classmethod
    def skip_checks(cls):
        super().skip_checks()
        if not CONF.compute_feature_enabled.spice_console:
            raise cls.skipException('SPICE console feature is disabled.')

    def tearDown(self):
        super().tearDown()
        # NOTE(zhufl): Because server_check_teardown will raise Exception
        # which will prevent other cleanup steps from being executed, so
        # server_check_teardown should be called after super's tearDown.
        self.server_check_teardown()

    @classmethod
    def setup_clients(cls):
        super().setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super().resource_setup()
        cls.server = cls.create_test_server(wait_until="ACTIVE")

    @decorators.idempotent_id('80f4460d-1a06-403c-9e93-cf434c70be05')
    def test_spice_direct(self):
        """Test accessing spice-direct console of server"""

        # Request a spice-direct console and validate the result. Any user can
        # do this.
        body = self.servers_client.get_remote_console(
            self.server['id'], console_type='spice-direct', protocol='spice')

        console_url = body['remote_console']['url']
        parts = urlparse.urlparse(console_url)
        qparams = urlparse.parse_qs(parts.query)
        self.assertIn('token', qparams)
        self.assertNotEmpty(qparams['token'])
        self.assertEqual(1, len(qparams['token']))

        self.assertEqual('spice', body['remote_console']['protocol'])
        self.assertEqual('spice-direct', body['remote_console']['type'])

        # For reasons best know to the python developers, the qparams values
        # are lists as documented at
        # https://docs.python.org/3/library/urllib.parse.html
        token = qparams['token'][0]

        # Turn that console token into hypervisor connection details. Only
        # admins can do this because its expected that the request is coming
        # from a proxy and we don't want to expose intimate hypervisor details
        # to all users.
        body = self.admin_servers_client.get_console_auth_token_details(
            token)

        console = body['console']
        self.assertEqual(self.server['id'], console['instance_uuid'])
        self.assertIn('port', console)
        self.assertIn('tls_port', console)
        self.assertIsNone(console['internal_access_path'])

        # Connect to the specified non-TLS port and verify we get back
        # a SPICE protocol greeting
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((console['host'], console['port']))

        # Send a client greeting
        #
        # ---- SpiceLinkMess ----
        # 4s    UINT32 magic value, must be REDQ
        # I     UINT32 major_version, must be 2
        # I     UINT32 minor_version, must be 2
        # I     UINT32 size number of bytes following this field to the end
        #              of this message.
        # I     UINT32 connection_id. In case of a new session (i.e., channel
        #              type is SPICE_CHANNEL_MAIN) this field is set to zero,
        #              and in response the server will allocate session id
        #              and will send it via the SpiceLinkReply message. In
        #              case of all other channel types, this field will be
        #              equal to the allocated session id.
        # B     UINT8  channel_type, we use main
        # B     UINT8  channel_id to connect to
        # I     UINT32 num_common_caps number of common client channel
        #              capabilities words
        # I     UINT32 num_channel_caps number of specific client channel
        #              capabilities words
        # I     UINT32 caps_offset location of the start of the capabilities
        #              vector given by the bytes offset from the “size”
        #              member (i.e., from the address of the “connection_id”
        #              member).
        # ...          capabilities
        sock.sendall(struct.pack(
            '<4sIIIIBBIIIII', self.magic, self.major, self.minor, 42 - 16,
            0, self.main_channel, 0, 1, 1, 18, self.common_caps,
            self.channel_caps))

        # ---- SpiceLinkReply ----
        # 4s     UINT32 magic value, must be equal to SPICE_MAGIC
        # I      UINT32 major_version, must be equal to SPICE_VERSION_MAJOR
        # I      UINT32 minor_version, must be equal to SPICE_VERSION_MINOR
        # I      UINT32 size number of bytes following this field to the end
        #               of this message.
        # I      UINT32 error code
        # ...
        buffered = sock.recv(20)
        self.assertIsNotNone(buffered)
        self.assertEqual(20, len(buffered))

        magic, major, minor, _, error = struct.unpack_from('<4sIIII', buffered)
        self.assertEqual(b'REDQ', magic)
        self.assertEqual(2, major)
        self.assertEqual(2, minor)
        self.assertEqual(0, error)
