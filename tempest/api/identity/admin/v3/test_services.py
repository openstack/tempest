#vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


class ServicesTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @attr(type='gate')
    def test_update_service(self):
        # Update description attribute of service
        name = rand_name('service-')
        type = rand_name('type--')
        description = rand_name('description-')
        resp, body = self.client.create_service(
            name, type, description=description)
        self.assertEqual('200', resp['status'])
        #Deleting the service created in this method
        self.addCleanup(self.client.delete_service, body['id'])

        s_id = body['id']
        resp1_desc = body['description']

        s_desc2 = rand_name('desc2-')
        resp, body = self.service_client.update_service(
            s_id, description=s_desc2)
        resp2_desc = body['description']
        self.assertEqual('200', resp['status'])
        self.assertNotEqual(resp1_desc, resp2_desc)

        #Get service
        resp, body = self.client.get_service(s_id)
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(resp2_desc, resp3_desc)


class ServicesTestXML(ServicesTestJSON):
    _interface = 'xml'
