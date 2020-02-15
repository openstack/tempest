# Copyright 2015 OpenStack Foundation
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

from tempest.api.network import base
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class RoutersTestDVR(base.BaseAdminNetworkTest):

    @classmethod
    def skip_checks(cls):
        super(RoutersTestDVR, cls).skip_checks()
        for ext in ['router', 'dvr']:
            if not utils.is_extension_enabled(ext, 'network'):
                msg = "%s extension not enabled." % ext
                raise cls.skipException(msg)
        # The check above will pass if api_extensions=all, which does
        # not mean DVR extension itself is present.
        # Instead, we have to check whether DVR is actually present by using
        # admin credentials to create router with distributed=True attribute
        # and checking for BadRequest exception and that the resulting router
        # has a distributed attribute.

    @classmethod
    def resource_setup(cls):
        super(RoutersTestDVR, cls).resource_setup()
        name = data_utils.rand_name('pretest-check')
        router = cls.admin_routers_client.create_router(name=name)
        cls.admin_routers_client.delete_router(router['router']['id'])
        if 'distributed' not in router['router']:
            msg = "'distributed' flag not found. DVR Possibly not enabled"
            raise cls.skipException(msg)

    @decorators.idempotent_id('08a2a0a8-f1e4-4b34-8e30-e522e836c44e')
    def test_distributed_router_creation(self):
        """Test distributed router creation

        Test uses administrative credentials to creates a
        DVR (Distributed Virtual Routing) router using the
        distributed=True.

        Acceptance
        The router is created and the "distributed" attribute is
        set to True
        """
        name = data_utils.rand_name('router')
        router = self.admin_routers_client.create_router(name=name,
                                                         distributed=True)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_routers_client.delete_router,
                        router['router']['id'])
        self.assertTrue(router['router']['distributed'])

    @decorators.idempotent_id('8a0a72b4-7290-4677-afeb-b4ffe37bc352')
    def test_centralized_router_creation(self):
        """Test centralized router creation

        Test uses administrative credentials to creates a
        CVR (Centralized Virtual Routing) router using the
        distributed=False.

        Acceptance
        The router is created and the "distributed" attribute is
        set to False, thus making it a "Centralized Virtual Router"
        as opposed to a "Distributed Virtual Router"
        """
        name = data_utils.rand_name('router')
        router = self.admin_routers_client.create_router(name=name,
                                                         distributed=False)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_routers_client.delete_router,
                        router['router']['id'])
        self.assertFalse(router['router']['distributed'])

    @decorators.idempotent_id('acd43596-c1fb-439d-ada8-31ad48ae3c2e')
    @testtools.skipUnless(utils.is_extension_enabled('l3-ha', 'network'),
                          'HA routers are not available.')
    def test_centralized_router_update_to_dvr(self):
        """Test centralized router update

        Test uses administrative credentials to creates a
        CVR (Centralized Virtual Routing) router using the
        distributed=False. Then it will "update" the router
        distributed attribute to True

        Acceptance
        The router is created and the "distributed" attribute is
        set to False. Once the router is updated, the distributed
        attribute will be set to True
        """
        name = data_utils.rand_name('router')
        project_id = self.routers_client.project_id
        # router needs to be in admin state down in order to be upgraded to DVR
        # l3ha routers are not upgradable to dvr, make it explicitly non ha
        router = self.admin_routers_client.create_router(name=name,
                                                         distributed=False,
                                                         admin_state_up=False,
                                                         ha=False,
                                                         project_id=project_id)
        router_id = router['router']['id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_routers_client.delete_router, router_id)
        self.assertFalse(router['router']['distributed'])
        router = self.admin_routers_client.update_router(
            router_id, distributed=True)
        self.assertTrue(router['router']['distributed'])
        show_body = self.admin_routers_client.show_router(router_id)
        self.assertTrue(show_body['router']['distributed'])
        show_body = self.routers_client.show_router(router_id)
        self.assertNotIn('distributed', show_body['router'])
