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

import netaddr
import testtools

from tempest.api.compute import base
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ServersTestJSON(base.BaseV2ComputeTest):
    disk_config = 'AUTO'
    volume_backed = False

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServersTestJSON, cls).resource_setup()
        validation_resources = cls.get_class_validation_resources(
            cls.os_primary)
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name(cls.__name__ + '-server')
        cls.password = data_utils.rand_password()
        disk_config = cls.disk_config
        server_initial = cls.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            name=cls.name,
            metadata=cls.meta,
            accessIPv4=cls.accessIPv4,
            accessIPv6=cls.accessIPv6,
            disk_config=disk_config,
            adminPass=cls.password,
            volume_backed=cls.volume_backed)
        cls.server = (cls.client.show_server(server_initial['id'])
                      ['server'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('5de47127-9977-400a-936f-abcfbec1218f')
    def test_verify_server_details(self):
        # Verify the specified server attributes are set correctly
        self.assertEqual(self.accessIPv4, self.server['accessIPv4'])
        # NOTE(maurosr): See http://tools.ietf.org/html/rfc5952 (section 4)
        # Here we compare directly with the canonicalized format.
        self.assertEqual(self.server['accessIPv6'],
                         str(netaddr.IPAddress(self.accessIPv6)))
        self.assertEqual(self.name, self.server['name'])
        if self.volume_backed:
            # Image is an empty string as per documentation
            self.assertEqual("", self.server['image'])
        else:
            self.assertEqual(self.image_ref, self.server['image']['id'])
        self.assert_flavor_equal(self.flavor_ref, self.server['flavor'])
        self.assertEqual(self.meta, self.server['metadata'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('9a438d88-10c6-4bcd-8b5b-5b6e25e1346f')
    def test_list_servers(self):
        # The created server should be in the list of all servers
        body = self.client.list_servers()
        servers = body['servers']
        found = [i for i in servers if i['id'] == self.server['id']]
        self.assertNotEmpty(found)

    @decorators.idempotent_id('585e934c-448e-43c4-acbf-d06a9b899997')
    def test_list_servers_with_detail(self):
        # The created server should be in the detailed list of all servers
        body = self.client.list_servers(detail=True)
        servers = body['servers']
        found = [i for i in servers if i['id'] == self.server['id']]
        self.assertNotEmpty(found)

    @decorators.idempotent_id('cbc0f52f-05aa-492b-bdc1-84b575ca294b')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_created_server_vcpus(self):
        # Verify that the number of vcpus reported by the instance matches
        # the amount stated by the flavor
        flavor = self.flavors_client.show_flavor(self.flavor_ref)['flavor']
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server, validation_resources),
            self.ssh_user,
            self.password,
            validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        output = linux_client.exec_command('grep -c ^processor /proc/cpuinfo')
        self.assertEqual(flavor['vcpus'], int(output))

    @decorators.idempotent_id('ac1ad47f-984b-4441-9274-c9079b7a0666')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_host_name_is_same_as_server_name(self):
        # Verify the instance host name is the same as the server name
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server, validation_resources),
            self.ssh_user,
            self.password,
            validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        hostname = linux_client.exec_command("hostname").rstrip()
        msg = ('Failed while verifying servername equals hostname. Expected '
               'hostname "%s" but got "%s".' %
               (self.name, hostname.split(".")[0]))
        # NOTE(zhufl): Some images will add postfix for the hostname, e.g.,
        # if hostname is "aaa", postfix ".novalocal" may be added to it, and
        # the hostname will be "aaa.novalocal" then, so we should ignore the
        # postfix when checking whether hostname equals self.name.
        self.assertEqual(self.name.lower(), hostname.split(".")[0], msg)


class ServersTestManualDisk(ServersTestJSON):
    disk_config = 'MANUAL'

    @classmethod
    def skip_checks(cls):
        super(ServersTestManualDisk, cls).skip_checks()
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)


class ServersTestBootFromVolume(ServersTestJSON):
    """Run the `ServersTestJSON` tests with a volume backed VM"""
    volume_backed = True

    @classmethod
    def skip_checks(cls):
        super(ServersTestBootFromVolume, cls).skip_checks()
        if not utils.get_service_list()['volume']:
            msg = "Volume service not enabled."
            raise cls.skipException(msg)
