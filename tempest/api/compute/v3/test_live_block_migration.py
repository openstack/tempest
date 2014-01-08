# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import random
import string

import testtools

from tempest.api.compute import base
from tempest import config
from tempest import exceptions
from tempest.test import attr


class LiveBlockMigrationV3TestJSON(base.BaseV3ComputeAdminTest):
    _host_key = 'os-extended-server-attributes:host'
    _interface = 'json'

    CONF = config.CONF

    @classmethod
    def setUpClass(cls):
        super(LiveBlockMigrationV3TestJSON, cls).setUpClass()

        cls.admin_hosts_client = cls.hosts_admin_client
        cls.admin_servers_client = cls.servers_admin_client

        cls.created_server_ids = []

    def _get_compute_hostnames(self):
        _resp, body = self.admin_hosts_client.list_hosts()
        return [
            host_record['host_name']
            for host_record in body
            if host_record['service'] == 'compute'
        ]

    def _get_server_details(self, server_id):
        _resp, body = self.admin_servers_client.get_server(server_id)
        return body

    def _get_host_for_server(self, server_id):
        return self._get_server_details(server_id)[self._host_key]

    def _migrate_server_to(self, server_id, dest_host):
        _resp, body = self.admin_servers_client.live_migrate_server(
            server_id, dest_host,
            self.config.compute_feature_enabled.
            block_migration_for_live_migration)
        return body

    def _get_host_other_than(self, host):
        for target_host in self._get_compute_hostnames():
            if host != target_host:
                return target_host

    def _get_non_existing_host_name(self):
        random_name = ''.join(
            random.choice(string.ascii_uppercase) for x in range(20))

        self.assertNotIn(random_name, self._get_compute_hostnames())

        return random_name

    def _get_server_status(self, server_id):
        return self._get_server_details(server_id)['status']

    def _get_an_active_server(self):
        for server_id in self.created_server_ids:
            if 'ACTIVE' == self._get_server_status(server_id):
                return server_id
        else:
            _, server = self.create_test_server(wait_until="ACTIVE")
            server_id = server['id']
            self.password = server['admin_password']
            self.password = 'password'
            self.created_server_ids.append(server_id)
            return server_id

    def _volume_clean_up(self, server_id, volume_id):
        resp, body = self.volumes_client.get_volume(volume_id)
        if body['status'] == 'in-use':
            self.servers_client.detach_volume(server_id, volume_id)
            self.volumes_client.wait_for_volume_status(volume_id, 'available')
        self.volumes_client.delete_volume(volume_id)

    @testtools.skipIf(not CONF.compute_feature_enabled.live_migration,
                      'Live migration not available')
    @attr(type='gate')
    def test_live_block_migration(self):
        # Live block migrate an instance to another host
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        server_id = self._get_an_active_server()
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)
        self._migrate_server_to(server_id, target_host)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(server_id))

    @testtools.skipIf(not CONF.compute_feature_enabled.live_migration,
                      'Live migration not available')
    @attr(type='gate')
    def test_invalid_host_for_migration(self):
        # Migrating to an invalid host should not change the status
        server_id = self._get_an_active_server()
        target_host = self._get_non_existing_host_name()

        self.assertRaises(exceptions.BadRequest, self._migrate_server_to,
                          server_id, target_host)
        self.assertEqual('ACTIVE', self._get_server_status(server_id))

    @testtools.skipIf(not CONF.compute_feature_enabled.live_migration or not
                      CONF.compute_feature_enabled.
                      block_migration_for_live_migration,
                      'Block Live migration not available')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migrate_cinder_iscsi,
                      'Block Live migration not configured for iSCSI')
    @attr(type='gate')
    def test_iscsi_volume(self):
        # Live block migrate an instance to another host
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        server_id = self._get_an_active_server()
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)

        resp, volume = self.volumes_client.create_volume(1,
                                                         display_name='test')

        self.volumes_client.wait_for_volume_status(volume['id'],
                                                   'available')
        self.addCleanup(self._volume_clean_up, server_id, volume['id'])

        # Attach the volume to the server
        self.servers_client.attach_volume(server_id, volume['id'],
                                          device='/dev/xvdb')
        self.volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self._migrate_server_to(server_id, target_host)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(server_id))

    @classmethod
    def tearDownClass(cls):
        for server_id in cls.created_server_ids:
            cls.servers_client.delete_server(server_id)

        super(LiveBlockMigrationV3TestJSON, cls).tearDownClass()


class LiveBlockMigrationV3TestXML(LiveBlockMigrationV3TestJSON):
    _host_key = (
        '{http://docs.openstack.org/compute/ext/'
        'extended_server_attributes/api/v3}host')
    _interface = 'xml'
