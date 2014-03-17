
# Copyright 2013 IBM Corp.
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


from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class EndpointsNegativeTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(EndpointsNegativeTestJSON, cls).setUpClass()
        cls.identity_client = cls.client
        cls.client = cls.endpoints_client
        cls.service_ids = list()
        s_name = data_utils.rand_name('service-')
        s_type = data_utils.rand_name('type--')
        s_description = data_utils.rand_name('description-')
        resp, cls.service_data = (
            cls.service_client.create_service(s_name, s_type,
                                              description=s_description))
        cls.service_id = cls.service_data['id']
        cls.service_ids.append(cls.service_id)

    @classmethod
    def tearDownClass(cls):
        for s in cls.service_ids:
            cls.service_client.delete_service(s)
        super(EndpointsNegativeTestJSON, cls).tearDownClass()

    @attr(type=['negative', 'gate'])
    def test_create_with_enabled_False(self):
        # Enabled should be a boolean, not a string like 'False'
        interface = 'public'
        url = data_utils.rand_name('url')
        region = data_utils.rand_name('region')
        self.assertRaises(exceptions.BadRequest, self.client.create_endpoint,
                          self.service_id, interface, url, region=region,
                          force_enabled='False')

    @attr(type=['negative', 'gate'])
    def test_create_with_enabled_True(self):
        # Enabled should be a boolean, not a string like 'True'
        interface = 'public'
        url = data_utils.rand_name('url')
        region = data_utils.rand_name('region')
        self.assertRaises(exceptions.BadRequest, self.client.create_endpoint,
                          self.service_id, interface, url, region=region,
                          force_enabled='True')

    def _assert_update_raises_bad_request(self, enabled):

        # Create an endpoint
        region1 = data_utils.rand_name('region')
        url1 = data_utils.rand_name('url')
        interface1 = 'public'
        resp, endpoint_for_update = (
            self.client.create_endpoint(self.service_id, interface1,
                                        url1, region=region1, enabled=True))
        self.addCleanup(self.client.delete_endpoint, endpoint_for_update['id'])

        self.assertRaises(exceptions.BadRequest, self.client.update_endpoint,
                          endpoint_for_update['id'], force_enabled=enabled)

    @attr(type=['negative', 'gate'])
    def test_update_with_enabled_False(self):
        # Enabled should be a boolean, not a string like 'False'
        self._assert_update_raises_bad_request('False')

    @attr(type=['negative', 'gate'])
    def test_update_with_enabled_True(self):
        # Enabled should be a boolean, not a string like 'True'
        self._assert_update_raises_bad_request('True')


class EndpointsNegativeTestXML(EndpointsNegativeTestJSON):
    _interface = 'xml'
