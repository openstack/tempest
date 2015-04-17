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

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest.api import utils
from tempest.common import fixed_network
from tempest import config
from tempest import test

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

        # Check to see if the alternate image ref actually exists...
        images_client = cls.images_client
        images = images_client.list_images()

        if cls.image_ref != cls.image_ref_alt and \
            any([image for image in images
                 if image['id'] == cls.image_ref_alt]):
            cls.multiple_images = True
        else:
            cls.image_ref_alt = cls.image_ref

        # Do some sanity checks here. If one of the images does
        # not exist, fail early since the tests won't work...
        try:
            cls.images_client.get_image(cls.image_ref)
        except lib_exc.NotFound:
            raise RuntimeError("Image %s (image_ref) was not found!" %
                               cls.image_ref)

        try:
            cls.images_client.get_image(cls.image_ref_alt)
        except lib_exc.NotFound:
            raise RuntimeError("Image %s (image_ref_alt) was not found!" %
                               cls.image_ref_alt)

        network = cls.get_tenant_network()
        if network:
            if network.get('name'):
                cls.fixed_network_name = network['name']
            else:
                cls.fixed_network_name = None
        else:
            cls.fixed_network_name = None
        network_kwargs = fixed_network.set_networks_kwarg(network)
        cls.s1_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s1 = cls.create_test_server(name=cls.s1_name,
                                        wait_until='ACTIVE',
                                        **network_kwargs)

        cls.s2_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s2 = cls.create_test_server(name=cls.s2_name,
                                        image_id=cls.image_ref_alt,
                                        wait_until='ACTIVE')

        cls.s3_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s3 = cls.create_test_server(name=cls.s3_name,
                                        flavor=cls.flavor_ref_alt,
                                        wait_until='ACTIVE')

    @test.idempotent_id('05e8a8e7-9659-459a-989d-92c2f501f4ba')
    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @test.attr(type='gate')
    def test_list_servers_filter_by_image(self):
        # Filter the list of servers by image
        params = {'image': self.image_ref}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('573637f5-7325-47bb-9144-3476d0416908')
    def test_list_servers_filter_by_flavor(self):
        # Filter the list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('9b067a7b-7fee-4f6a-b29c-be43fe18fc5a')
    def test_list_servers_filter_by_server_name(self):
        # Filter the list of servers by server name
        params = {'name': self.s1_name}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('ca78e20e-fddb-4ce6-b7f7-bcbf8605e66e')
    def test_list_servers_filter_by_server_status(self):
        # Filter the list of servers by server status
        params = {'status': 'active'}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('451dbbb2-f330-4a9f-b0e1-5f5d2cb0f34c')
    def test_list_servers_filter_by_shutoff_status(self):
        # Filter the list of servers by server shutoff status
        params = {'status': 'shutoff'}
        self.client.stop(self.s1['id'])
        self.client.wait_for_server_status(self.s1['id'],
                                           'SHUTOFF')
        body = self.client.list_servers(params)
        self.client.start(self.s1['id'])
        self.client.wait_for_server_status(self.s1['id'],
                                           'ACTIVE')
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('614cdfc1-d557-4bac-915b-3e67b48eee76')
    def test_list_servers_filter_by_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 1}
        servers = self.client.list_servers(params)
        self.assertEqual(1, len([x for x in servers['servers'] if 'id' in x]))

    @test.attr(type='gate')
    @test.idempotent_id('b1495414-2d93-414c-8019-849afe8d319e')
    def test_list_servers_filter_by_zero_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 0}
        servers = self.client.list_servers(params)
        self.assertEqual(0, len(servers['servers']))

    @test.attr(type='gate')
    @test.idempotent_id('37791bbd-90c0-4de0-831e-5f38cba9c6b3')
    def test_list_servers_filter_by_exceed_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 100000}
        servers = self.client.list_servers(params)
        all_servers = self.client.list_servers()
        self.assertEqual(len([x for x in all_servers['servers'] if 'id' in x]),
                         len([x for x in servers['servers'] if 'id' in x]))

    @test.idempotent_id('b3304c3b-97df-46d2-8cd3-e2b6659724e7')
    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @test.attr(type='gate')
    def test_list_servers_detailed_filter_by_image(self):
        # Filter the detailed list of servers by image
        params = {'image': self.image_ref}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('80c574cc-0925-44ba-8602-299028357dd9')
    def test_list_servers_detailed_filter_by_flavor(self):
        # Filter the detailed list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('f9eb2b70-735f-416c-b260-9914ac6181e4')
    def test_list_servers_detailed_filter_by_server_name(self):
        # Filter the detailed list of servers by server name
        params = {'name': self.s1_name}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('de2612ab-b7dd-4044-b0b1-d2539601911f')
    def test_list_servers_detailed_filter_by_server_status(self):
        # Filter the detailed list of servers by server status
        params = {'status': 'active'}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        test_ids = [s['id'] for s in (self.s1, self.s2, self.s3)]

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))
        self.assertEqual(['ACTIVE'] * 3, [x['status'] for x in servers
                                          if x['id'] in test_ids])

    @test.attr(type='gate')
    @test.idempotent_id('e9f624ee-92af-4562-8bec-437945a18dcb')
    def test_list_servers_filtered_by_name_wildcard(self):
        # List all servers that contains '-instance' in name
        params = {'name': '-instance'}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[6:-1]

        params = {'name': part_name}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('24a89b0c-0d55-4a28-847f-45075f19b27b')
    def test_list_servers_filtered_by_name_regex(self):
        # list of regex that should match s1, s2 and s3
        regexes = ['^.*\-instance\-[0-9]+$', '^.*\-instance\-.*$']
        for regex in regexes:
            params = {'name': regex}
            body = self.client.list_servers(params)
            servers = body['servers']

            self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[-10:]

        params = {'name': part_name}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('43a1242e-7b31-48d1-88f2-3f72aa9f2077')
    def test_list_servers_filtered_by_ip(self):
        # Filter servers by ip
        # Here should be listed 1 server
        if not self.fixed_network_name:
            msg = 'fixed_network_name needs to be configured to run this test'
            raise self.skipException(msg)
        self.s1 = self.client.get_server(self.s1['id'])
        ip = self.s1['addresses'][self.fixed_network_name][0]['addr']
        params = {'ip': ip}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.skip_because(bug="1182883",
                             condition=CONF.service_available.neutron)
    @test.attr(type='gate')
    @test.idempotent_id('a905e287-c35e-42f2-b132-d02b09f3654a')
    def test_list_servers_filtered_by_ip_regex(self):
        # Filter servers by regex ip
        # List all servers filtered by part of ip address.
        # Here should be listed all servers
        if not self.fixed_network_name:
            msg = 'fixed_network_name needs to be configured to run this test'
            raise self.skipException(msg)
        self.s1 = self.client.get_server(self.s1['id'])
        ip = self.s1['addresses'][self.fixed_network_name][0]['addr'][0:-3]
        params = {'ip': ip}
        body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('67aec2d0-35fe-4503-9f92-f13272b867ed')
    def test_list_servers_detailed_limit_results(self):
        # Verify only the expected number of detailed results are returned
        params = {'limit': 1}
        servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))
