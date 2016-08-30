# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.image.v2 import schemas_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSchemasClient(base.BaseServiceTest):
    FAKE_SHOW_SCHEMA = {
        "links": [
            {
                "href": "{schema}",
                "rel": "describedby"
            }
        ],
        "name": "members",
        "properties": {
            "members": {
                "items": {
                    "name": "member",
                    "properties": {
                        "created_at": {
                            "description": ("Date and time of image member"
                                            " creation"),
                            "type": "string"
                        },
                        "image_id": {
                            "description": "An identifier for the image",
                            "pattern": ("^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}"
                                        "-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}"
                                        "-([0-9a-fA-F]){12}$"),
                            "type": "string"
                        },
                        "member_id": {
                            "description": ("An identifier for the image"
                                            " member (tenantId)"),
                            "type": "string"
                        },
                        "schema": {
                            "type": "string"
                        },
                        "status": {
                            "description": "The status of this image member",
                            "enum": [
                                "pending",
                                "accepted",
                                "rejected"
                            ],
                            "type": "string"
                        },
                        "updated_at": {
                            "description": ("Date and time of last"
                                            " modification of image member"),
                            "type": "string"
                        }
                    }
                },
                "type": "array"
            },
            "schema": {
                "type": "string"
            }
        }
    }

    def setUp(self):
        super(TestSchemasClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = schemas_client.SchemasClient(fake_auth,
                                                   'image', 'regionOne')

    def _test_show_schema(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_schema,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_SCHEMA,
            bytes_body,
            schema="member")

    def test_show_schema_with_str_body(self):
        self._test_show_schema()

    def test_show_schema_with_bytes_body(self):
        self._test_show_schema(bytes_body=True)
