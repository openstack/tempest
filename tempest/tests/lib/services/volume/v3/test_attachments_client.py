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

from tempest.lib.services.volume.v3 import attachments_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base

from oslo_utils.fixture import uuidsentinel as uuids


class TestAttachmentsClient(base.BaseServiceTest):

    FAKE_ATTACHMENT_INFO = {
        "attachment": {
            "status": "attaching",
            "detached_at": "2015-09-16T09:28:52.000000",
            "connection_info": {},
            "attached_at": "2015-09-16T09:28:52.000000",
            "attach_mode": "ro",
            "instance": uuids.instance_id,
            "volume_id": uuids.volume_id,
            "id": uuids.id,
        }
    }

    def setUp(self):
        super(TestAttachmentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = attachments_client.AttachmentsClient(fake_auth,
                                                           'volume',
                                                           'regionOne')

    def test_show_attachment(self):
        self.check_service_client_function(
            self.client.show_attachment,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ATTACHMENT_INFO, attachment_id=uuids.id)
