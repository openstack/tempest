# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import re
import sys

import nose
import unittest2 as unittest

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest import openstack
from tempest.tests import compute
from tempest.tests.compute.base import BaseComputeTest


class ListServersNegativeTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ListServersNegativeTest, cls).setUpClass()
        cls.client = cls.servers_client
        cls.servers = []

        if compute.MULTI_USER:
            if cls.config.compute.allow_tenant_isolation:
                creds = cls._get_isolated_creds()
                username, tenant_name, password = creds
                cls.alt_manager = openstack.Manager(username=username,
                                                    password=password,
                                                    tenant_name=tenant_name)
            else:
                # Use the alt_XXX credentials in the config file
                cls.alt_manager = openstack.AltManager()
            cls.alt_client = cls.alt_manager.servers_client

        # Under circumstances when there is not a tenant/user
        # created for the test case, the test case checks
        # to see if there are existing servers for the
        # either the normal user/tenant or the alt user/tenant
        # and if so, the whole test is skipped. We do this
        # because we assume a baseline of no servers at the
        # start of the test instead of destroying any existing
        # servers.
        resp, body = cls.client.list_servers()
        servers = body['servers']
        num_servers = len(servers)
        if num_servers > 0:
            username = cls.os.username
            tenant_name = cls.os.tenant_name
            msg = ("User/tenant %(username)s/%(tenant_name)s already have "
                   "existing server instances. Skipping test.") % locals()
            raise nose.SkipTest(msg)

        resp, body = cls.alt_client.list_servers()
        servers = body['servers']
        num_servers = len(servers)
        if num_servers > 0:
            username = cls.alt_manager.username
            tenant_name = cls.alt_manager.tenant_name
            msg = ("Alt User/tenant %(username)s/%(tenant_name)s already have "
                   "existing server instances. Skipping test.") % locals()
            raise nose.SkipTest(msg)

        # The following servers are created for use
        # by the test methods in this class. These
        # servers are cleaned up automatically in the
        # tearDownClass method of the super-class.
        cls.existing_fixtures = []
        cls.deleted_fixtures = []
        for x in xrange(2):
            srv = cls.create_server()
            cls.existing_fixtures.append(srv)

        srv = cls.create_server()
        cls.client.delete_server(srv['id'])
        # We ignore errors on termination because the server may
        # be put into ERROR status on a quick spawn, then delete,
        # as the compute node expects the instance local status
        # to be spawning, not deleted. See LP Bug#1061167
        cls.client.wait_for_server_termination(srv['id'],
                                               ignore_error=True)
        cls.deleted_fixtures.append(srv)

    def test_list_servers_with_a_deleted_server(self):
        """Verify deleted servers do not show by default in list servers"""
        # List servers and verify server not returned
        resp, body = self.client.list_servers()
        servers = body['servers']
        deleted_ids = [s['id'] for s in self.deleted_fixtures]
        actual = [srv for srv in servers
                  if srv['id'] in deleted_ids]
        self.assertEqual('200', resp['status'])
        self.assertEqual([], actual)

    def test_list_servers_by_non_existing_image(self):
        """Listing servers for a non existing image returns empty list"""
        non_existing_image = '1234abcd-zzz0-aaa9-ppp3-0987654abcde'
        resp, body = self.client.list_servers(dict(image=non_existing_image))
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    def test_list_servers_by_non_existing_flavor(self):
        """Listing servers by non existing flavor returns empty list"""
        non_existing_flavor = 1234
        resp, body = self.client.list_servers(dict(flavor=non_existing_flavor))
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    def test_list_servers_by_non_existing_server_name(self):
        """Listing servers for a non existent server name returns empty list"""
        non_existing_name = 'junk_server_1234'
        resp, body = self.client.list_servers(dict(name=non_existing_name))
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    @unittest.skip("Skip until bug 1061712 is resolved")
    def test_list_servers_status_non_existing(self):
        """Return an empty list when invalid status is specified"""
        non_existing_status = 'BALONEY'
        resp, body = self.client.list_servers(dict(status=non_existing_status))
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    def test_list_servers_by_limits(self):
        """List servers by specifying limits"""
        resp, body = self.client.list_servers({'limit': 1})
        self.assertEqual('200', resp['status'])
        self.assertEqual(1, len(body['servers']))

    def test_list_servers_by_limits_greater_than_actual_count(self):
        """List servers by specifying a greater value for limit"""
        resp, body = self.client.list_servers({'limit': 100})
        self.assertEqual('200', resp['status'])
        self.assertEqual(len(self.existing_fixtures), len(body['servers']))

    def test_list_servers_by_limits_pass_string(self):
        """Return an error if a string value is passed for limit"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'limit': 'testing'})

    def test_list_servers_by_limits_pass_negative_value(self):
        """Return an error if a negative value for limit is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'limit': -1})

    def test_list_servers_by_changes_since(self):
        """Servers are listed by specifying changes-since date"""
        resp, body = self.client.list_servers(
                         {'changes-since': '2011-01-01T12:34:00Z'})
        self.assertEqual('200', resp['status'])
        # changes-since returns all instances, including deleted.
        num_expected = (len(self.existing_fixtures) +
                        len(self.deleted_fixtures))
        self.assertEqual(num_expected, len(body['servers']))

    def test_list_servers_by_changes_since_invalid_date(self):
        """Return an error when invalid date format is passed"""
        self.assertRaises(exceptions.BadRequest, self.client.list_servers,
                          {'changes-since': '2011/01/01'})

    def test_list_servers_by_changes_since_future_date(self):
        """Return an empty list when a date in the future is passed"""
        resp, body = self.client.list_servers(
                         {'changes-since': '2051-01-01T12:34:00Z'})
        self.assertEqual('200', resp['status'])
        self.assertEqual(0, len(body['servers']))

    def test_list_servers_detail_server_is_deleted(self):
        """Server details are not listed for a deleted server"""
        deleted_ids = [s['id'] for s in self.deleted_fixtures]
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        actual = [srv for srv in servers
                  if srv['id'] in deleted_ids]
        self.assertEqual('200', resp['status'])
        self.assertEqual([], actual)
