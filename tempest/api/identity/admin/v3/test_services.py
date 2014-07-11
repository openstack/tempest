# Copyright 2013 OpenStack Foundation
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
from tempest import test


class ServicesTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @test.attr(type='gate')
    def test_update_service(self):
        # Update description attribute of service
        name = data_utils.rand_name('service-')
        serv_type = data_utils.rand_name('type--')
        desc = data_utils.rand_name('description-')
        _, body = self.service_client.create_service(name, serv_type,
                                                     description=desc)
        # Deleting the service created in this method
        self.addCleanup(self.service_client.delete_service, body['id'])

        s_id = body['id']
        resp1_desc = body['description']

        s_desc2 = data_utils.rand_name('desc2-')
        _, body = self.service_client.update_service(
            s_id, description=s_desc2)
        resp2_desc = body['description']
        self.assertNotEqual(resp1_desc, resp2_desc)

        # Get service
        _, body = self.service_client.get_service(s_id)
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(resp2_desc, resp3_desc)


class ServicesTestXML(ServicesTestJSON):
    _interface = 'xml'
