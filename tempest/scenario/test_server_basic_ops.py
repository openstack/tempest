# Copyright 2012 OpenStack Foundation
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

import json
import re

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF


class TestServerBasicOps(manager.ScenarioTest):

    """The test suite for server basic operations

    This smoke test case follows this basic set of operations:
     * Create a keypair for use in launching an instance
     * Create a security group to control network access in instance
     * Add simple permissive rules to the security group
     * Launch an instance
     * Perform ssh to instance
     * Verify metadata service
     * Verify metadata on config_drive
     * Terminate the instance
    """

    def setUp(self):
        super(TestServerBasicOps, self).setUp()
        self.run_ssh = CONF.validation.run_validation
        self.ssh_user = CONF.validation.image_ssh_user

    def verify_ssh(self, keypair):
        if self.run_ssh:
            # Obtain a floating IP if floating_ips is enabled
            if (CONF.network_feature_enabled.floating_ips and
                CONF.network.floating_network_name):
                self.ip = self.create_floating_ip(self.instance)['ip']
            else:
                server = self.servers_client.show_server(
                    self.instance['id'])['server']
                self.ip = self.get_server_ip(server)
            # Check ssh
            self.ssh_client = self.get_remote_client(
                ip_address=self.ip,
                username=self.ssh_user,
                private_key=keypair['private_key'],
                server=self.instance)

    def verify_metadata(self):
        if self.run_ssh and CONF.compute_feature_enabled.metadata_service:
            # Verify metadata service
            md_url = 'http://169.254.169.254/latest/meta-data/public-ipv4'

            def exec_cmd_and_verify_output():
                cmd = 'curl ' + md_url
                result = self.ssh_client.exec_command(cmd)
                if result:
                    msg = ('Failed while verifying metadata on server. Result '
                           'of command "%s" is NOT "%s".' % (cmd, self.ip))
                    self.assertEqual(self.ip, result, msg)
                    return 'Verification is successful!'

            if not test_utils.call_until_true(exec_cmd_and_verify_output,
                                              CONF.compute.build_timeout,
                                              CONF.compute.build_interval):
                raise exceptions.TimeoutException('Timed out while waiting to '
                                                  'verify metadata on server. '
                                                  '%s is empty.' % md_url)

            # Also, test a POST
            md_url = 'http://169.254.169.254/openstack/2013-10-17/password'
            data = data_utils.arbitrary_string(100)
            cmd = 'curl -X POST -d ' + data + ' ' + md_url
            self.ssh_client.exec_command(cmd)
            result = self.servers_client.show_password(self.instance['id'])
            self.assertEqual(data, result['password'])

    def _mount_config_drive(self):
        cmd_blkid = 'blkid | grep -i config-2'
        result = self.ssh_client.exec_command(cmd_blkid)
        dev_name = re.match('([^:]+)', result).group()
        self.ssh_client.exec_command('sudo mount %s /mnt' % dev_name)

    def _unmount_config_drive(self):
        self.ssh_client.exec_command('sudo umount /mnt')

    def verify_metadata_on_config_drive(self):
        if self.run_ssh and CONF.compute_feature_enabled.config_drive:
            # Verify metadata on config_drive
            self._mount_config_drive()
            cmd_md = 'sudo cat /mnt/openstack/latest/meta_data.json'
            result = self.ssh_client.exec_command(cmd_md)
            self._unmount_config_drive()
            result = json.loads(result)
            self.assertIn('meta', result)
            msg = ('Failed while verifying metadata on config_drive on server.'
                   ' Result of command "%s" is NOT "%s".' % (cmd_md, self.md))
            self.assertEqual(self.md, result['meta'], msg)

    def verify_networkdata_on_config_drive(self):
        if self.run_ssh and CONF.compute_feature_enabled.config_drive:
            # Verify network data on config_drive
            self._mount_config_drive()
            cmd_md = 'sudo cat /mnt/openstack/latest/network_data.json'
            result = self.ssh_client.exec_command(cmd_md)
            self._unmount_config_drive()
            result = json.loads(result)
            self.assertIn('services', result)
            self.assertIn('links', result)
            self.assertIn('networks', result)
            # TODO(clarkb) construct network_data from known network
            # instance info and do direct comparison.

    @decorators.idempotent_id('7fff3fb3-91d8-4fd0-bd7d-0204f1f180ba')
    @decorators.attr(type='smoke')
    @utils.services('compute', 'network')
    def test_server_basic_ops(self):
        keypair = self.create_keypair()
        security_group = self._create_security_group()
        self.md = {'meta1': 'data1', 'meta2': 'data2', 'metaN': 'dataN'}
        self.instance = self.create_server(
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}],
            config_drive=CONF.compute_feature_enabled.config_drive,
            metadata=self.md)
        self.verify_ssh(keypair)
        self.verify_metadata()
        self.verify_metadata_on_config_drive()
        self.verify_networkdata_on_config_drive()
        self.servers_client.delete_server(self.instance['id'])
        waiters.wait_for_server_termination(
            self.servers_client, self.instance['id'], ignore_error=False)
