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
import testtools

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common import fixed_network
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


CONF = config.CONF


class ListServerFiltersTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, dhcp=True)
        super(ListServerFiltersTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ListServerFiltersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ListServerFiltersTestJSON, cls).resource_setup()

        network = cls.get_tenant_network()
        if network:
            cls.fixed_network_name = network.get('name')
        else:
            cls.fixed_network_name = None
        network_kwargs = fixed_network.set_networks_kwarg(network)
        cls.s1_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s1 = cls.create_test_server(name=cls.s1_name, **network_kwargs)

        cls.s2_name = data_utils.rand_name(cls.__name__ + '-instance')
        # If image_ref_alt is "" or None then we still want to boot a server
        # but we rely on `testtools.skipUnless` decorator to actually skip
        # the irrelevant tests.
        cls.s2 = cls.create_test_server(
            name=cls.s2_name, image_id=cls.image_ref_alt or cls.image_ref)

        cls.s3_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s3 = cls.create_test_server(name=cls.s3_name,
                                        flavor=cls.flavor_ref_alt,
                                        wait_until='ACTIVE')

        waiters.wait_for_server_status(cls.client, cls.s1['id'],
                                       'ACTIVE')
        waiters.wait_for_server_status(cls.client, cls.s2['id'],
                                       'ACTIVE')

    @decorators.idempotent_id('05e8a8e7-9659-459a-989d-92c2f501f4ba')
    @testtools.skipUnless(CONF.compute.image_ref != CONF.compute.image_ref_alt,
                          "Need distinct images to run this test")
    def test_list_servers_filter_by_image(self):
        # Filter the list of servers by image
        params = {'image': self.image_ref}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('573637f5-7325-47bb-9144-3476d0416908')
    def test_list_servers_filter_by_flavor(self):
        # Filter the list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('9b067a7b-7fee-4f6a-b29c-be43fe18fc5a')
    def test_list_servers_filter_by_server_name(self):
        # Filter the list of servers by server name
        params = {'name': self.s1_name}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.idempotent_id('ca78e20e-fddb-4ce6-b7f7-bcbf8605e66e')
    def test_list_servers_filter_by_active_status(self):
        # Filter the list of servers by server active status
        params = {'status': 'active'}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('451dbbb2-f330-4a9f-b0e1-5f5d2cb0f34c')
    def test_list_servers_filter_by_shutoff_status(self):
        # Filter the list of servers by server shutoff status
        params = {'status': 'shutoff'}
        self.client.stop_server(self.s1['id'])
        waiters.wait_for_server_status(self.client, self.s1['id'],
                                       'SHUTOFF')
        body = self.client.list_servers(**params)
        self.client.start_server(self.s1['id'])
        waiters.wait_for_server_status(self.client, self.s1['id'],
                                       'ACTIVE')
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('614cdfc1-d557-4bac-915b-3e67b48eee76')
    def test_list_servers_filter_by_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 1}
        servers = self.client.list_servers(**params)
        self.assertEqual(1, len([x for x in servers['servers'] if 'id' in x]))

    @decorators.idempotent_id('b1495414-2d93-414c-8019-849afe8d319e')
    def test_list_servers_filter_by_zero_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 0}
        servers = self.client.list_servers(**params)
        self.assertEmpty(servers['servers'])

    @decorators.idempotent_id('37791bbd-90c0-4de0-831e-5f38cba9c6b3')
    def test_list_servers_filter_by_exceed_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 100000}
        servers = self.client.list_servers(**params)
        all_servers = self.client.list_servers()
        self.assertEqual(len([x for x in all_servers['servers'] if 'id' in x]),
                         len([x for x in servers['servers'] if 'id' in x]))

    @decorators.idempotent_id('b3304c3b-97df-46d2-8cd3-e2b6659724e7')
    @testtools.skipUnless(CONF.compute.image_ref != CONF.compute.image_ref_alt,
                          "Need distinct images to run this test")
    def test_list_servers_detailed_filter_by_image(self):
        # Filter the detailed list of servers by image
        params = {'image': self.image_ref}
        body = self.client.list_servers(detail=True, **params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('80c574cc-0925-44ba-8602-299028357dd9')
    def test_list_servers_detailed_filter_by_flavor(self):
        # Filter the detailed list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        body = self.client.list_servers(detail=True, **params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @decorators.idempotent_id('f9eb2b70-735f-416c-b260-9914ac6181e4')
    def test_list_servers_detailed_filter_by_server_name(self):
        # Filter the detailed list of servers by server name
        params = {'name': self.s1_name}
        body = self.client.list_servers(detail=True, **params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.idempotent_id('de2612ab-b7dd-4044-b0b1-d2539601911f')
    def test_list_servers_detailed_filter_by_server_status(self):
        # Filter the detailed list of servers by server status
        params = {'status': 'active'}
        body = self.client.list_servers(detail=True, **params)
        servers = body['servers']
        test_ids = [s['id'] for s in (self.s1, self.s2, self.s3)]

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))
        self.assertEqual(['ACTIVE'] * 3, [x['status'] for x in servers
                                          if x['id'] in test_ids])

    @decorators.idempotent_id('e9f624ee-92af-4562-8bec-437945a18dcb')
    def test_list_servers_filtered_by_name_wildcard(self):
        # List all servers that contains '-instance' in name
        params = {'name': '-instance'}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[6:-1]

        params = {'name': part_name}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.idempotent_id('24a89b0c-0d55-4a28-847f-45075f19b27b')
    def test_list_servers_filtered_by_name_regex(self):
        # list of regex that should match s1, s2 and s3
        regexes = [r'^.*\-instance\-[0-9]+$', r'^.*\-instance\-.*$']
        for regex in regexes:
            params = {'name': regex}
            body = self.client.list_servers(**params)
            servers = body['servers']

            self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[-10:]

        params = {'name': part_name}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.idempotent_id('43a1242e-7b31-48d1-88f2-3f72aa9f2077')
    def test_list_servers_filtered_by_ip(self):
        # Filter servers by ip
        # Here should be listed 1 server
        if not self.fixed_network_name:
            msg = 'fixed_network_name needs to be configured to run this test'
            raise self.skipException(msg)

        # list servers filter by ip is something "regexp match", i.e,
        # filter by "10.1.1.1" will return both "10.1.1.1" and "10.1.1.10".
        # so here look for the longest server ip, and filter by that ip,
        # so as to ensure only one server is returned.
        ip_list = {}
        self.s1 = self.client.show_server(self.s1['id'])['server']
        # Get first ip address in spite of v4 or v6
        ip_addr = self.s1['addresses'][self.fixed_network_name][0]['addr']
        ip_list[ip_addr] = self.s1['id']

        self.s2 = self.client.show_server(self.s2['id'])['server']
        ip_addr = self.s2['addresses'][self.fixed_network_name][0]['addr']
        ip_list[ip_addr] = self.s2['id']

        self.s3 = self.client.show_server(self.s3['id'])['server']
        ip_addr = self.s3['addresses'][self.fixed_network_name][0]['addr']
        ip_list[ip_addr] = self.s3['id']

        longest_ip = max([[len(ip), ip] for ip in ip_list])[1]
        params = {'ip': longest_ip}
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(ip_list[longest_ip], map(lambda x: x['id'], servers))
        del ip_list[longest_ip]
        for ip in ip_list:
            self.assertNotIn(ip_list[ip], map(lambda x: x['id'], servers))

    @decorators.skip_because(bug="1540645")
    @decorators.idempotent_id('a905e287-c35e-42f2-b132-d02b09f3654a')
    def test_list_servers_filtered_by_ip_regex(self):
        # Filter servers by regex ip
        # List all servers filtered by part of ip address.
        # Here should be listed all servers
        if not self.fixed_network_name:
            msg = 'fixed_network_name needs to be configured to run this test'
            raise self.skipException(msg)
        self.s1 = self.client.show_server(self.s1['id'])['server']
        addr_spec = self.s1['addresses'][self.fixed_network_name][0]
        ip = addr_spec['addr'][0:-3]
        if addr_spec['version'] == 4:
            params = {'ip': ip}
        else:
            params = {'ip6': ip}
        # capture all servers in case something goes wrong
        all_servers = self.client.list_servers(detail=True)
        body = self.client.list_servers(**params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers),
                      "%s not found in %s, all servers %s" %
                      (self.s1_name, servers, all_servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers),
                      "%s not found in %s, all servers %s" %
                      (self.s2_name, servers, all_servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers),
                      "%s not found in %s, all servers %s" %
                      (self.s3_name, servers, all_servers))

    @decorators.idempotent_id('67aec2d0-35fe-4503-9f92-f13272b867ed')
    def test_list_servers_detailed_limit_results(self):
        # Verify only the expected number of detailed results are returned
        params = {'limit': 1}
        servers = self.client.list_servers(detail=True, **params)
        self.assertEqual(1, len(servers['servers']))
