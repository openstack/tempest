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

    FAKE_SHOW_SCHEMA_IMAGE = {
        "additionalProperties": {
            "type": "string"
        },
        "links": [
            {
                "href": "{self}",
                "rel": "self"
            },
            {
                "href": "{file}",
                "rel": "enclosure"
            },
            {
                "href": "{schema}",
                "rel": "describedby"
            }
        ],
        "name": "image",
        "properties": {
            "architecture": {
                "description": "Operating system architecture as "
                               "specified in https://docs.openstack.org/"
                               "python-glanceclient/latest/cli"
                               "/property-keys.html",
                "is_base": False,
                "type": "string"
            },
            "checksum": {
                "description": "md5 hash of image contents.",
                "maxLength": 32,
                "readOnly": True,
                "type": [
                    "null",
                    "string"
                ]
            },
            "container_format": {
                "description": "Format of the container",
                "enum": [
                    None,
                    "ami",
                    "ari",
                    "aki",
                    "bare",
                    "ovf",
                    "ova",
                    "docker"
                ],
                "type": [
                    "null",
                    "string"
                ]
            },
            "created_at": {
                "description": "Date and time of image registration",
                "readOnly": True,
                "type": "string"
            },
            "direct_url": {
                "description": "URL to access the image file "
                               "kept in external store",
                "readOnly": True,
                "type": "string"
            },
            "disk_format": {
                "description": "Format of the disk",
                "enum": [
                    None,
                    "ami",
                    "ari",
                    "aki",
                    "vhd",
                    "vhdx",
                    "vmdk",
                    "raw",
                    "qcow2",
                    "vdi",
                    "iso",
                    "ploop"
                ],
                "type": [
                    "null",
                    "string"
                ]
            },
            "file": {
                "description": "An image file url",
                "readOnly": True,
                "type": "string"
            },
            "id": {
                "description": "An identifier for the image",
                "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F])"
                           "{4}-([0-9a-fA-F]){4}-([0-9a-fA-F])"
                           "{4}-([0-9a-fA-F]){12}$",
                "type": "string"
            },
            "instance_uuid": {
                "description": "Metadata which can be used to record which"
                               " instance this image is associated with. "
                               "(Informational only, does not create "
                               "an instance snapshot.)",
                "is_base": False,
                "type": "string"
            },
            "kernel_id": {
                "description": "ID of image stored in Glance that should "
                               "be used as the kernel when booting an "
                               "AMI-style image.",
                "is_base": False,
                "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-"
                           "([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-("
                           "[0-9a-fA-F]){12}$",
                "type": [
                    "null",
                    "string"
                ]
            },
            "locations": {
                "description": "A set of URLs to access the image file "
                               "kept in external store",
                "items": {
                    "properties": {
                        "metadata": {
                            "type": "object"
                        },
                        "url": {
                            "maxLength": 255,
                            "type": "string"
                        }
                    },
                    "required": [
                        "url",
                        "metadata"
                    ],
                    "type": "object"
                },
                "type": "array"
            },
            "min_disk": {
                "description": "Amount of disk space (in GB) "
                               "required to boot image.",
                "type": "integer"
            },
            "min_ram": {
                "description": "Amount of ram (in MB) required "
                               "to boot image.",
                "type": "integer"
            },
            "name": {
                "description": "Descriptive name for the image",
                "maxLength": 255,
                "type": [
                    "null",
                    "string"
                ]
            },
            "os_distro": {
                "description": "Common name of operating system distribution "
                               "as specified in https://docs.openstack.org/"
                               "python-glanceclient/latest/cli/"
                               "property-keys.html",
                "is_base": False,
                "type": "string"
            },
            "os_hash_algo": {
                "description": "Algorithm to calculate the os_hash_value",
                "maxLength": 64,
                "readOnly": True,
                "type": [
                    "null",
                    "string"
                ]
            },
            "os_hash_value": {
                "description": "Hexdigest of the image contents "
                               "using the algorithm specified by "
                               "the os_hash_algo",
                "maxLength": 128,
                "readOnly": True,
                "type": [
                    "null",
                    "string"
                ]
            },
            "os_hidden": {
                "description": "If true, image will not appear in default"
                               " image list response.",
                "type": "boolean"
            },
            "os_version": {
                "description": "Operating system version as specified by "
                               "the distributor",
                "is_base": False,
                "type": "string"
            },
            "owner": {
                "description": "Owner of the image",
                "maxLength": 255,
                "type": [
                    "null",
                    "string"
                ]
            },
            "protected": {
                "description": "If true, image will not be deletable.",
                "type": "boolean"
            },
            "ramdisk_id": {
                "description": "ID of image stored in Glance that should"
                               " be used as the ramdisk when booting an "
                               "AMI-style image.",
                "is_base": False,
                "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F])"
                           "{4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$",
                "type": [
                    "null",
                    "string"
                ]
            },
            "schema": {
                "description": "An image schema url",
                "readOnly": True,
                "type": "string"
            },
            "self": {
                "description": "An image self url",
                "readOnly": True,
                "type": "string"
            },
            "size": {
                "description": "Size of image file in bytes",
                "readOnly": True,
                "type": [
                    "null",
                    "integer"
                ]
            },
            "status": {
                "description": "Status of the image",
                "enum": [
                    "queued",
                    "saving",
                    "active",
                    "killed",
                    "deleted",
                    "pending_delete",
                    "deactivated",
                    "uploading",
                    "importing"
                ],
                "readOnly": True,
                "type": "string"
            },
            "tags": {
                "description": "List of strings related to the image",
                "items": {
                    "maxLength": 255,
                    "type": "string"
                },
                "type": "array"
            },
            "updated_at": {
                "description": "Date and time of the last image modification",
                "readOnly": True,
                "type": "string"
            },
            "virtual_size": {
                "description": "Virtual size of image in bytes",
                "readOnly": True,
                "type": [
                    "null",
                    "integer"
                ]
            },
            "visibility": {
                "description": "Scope of image accessibility",
                "enum": [
                    "public",
                    "private"
                ],
                "type": "string"
            }
        }
    }

    def setUp(self):
        super(TestSchemasClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = schemas_client.SchemasClient(fake_auth,
                                                   'image', 'regionOne')

    def _test_show_schema_members(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_schema,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_SCHEMA,
            bytes_body,
            schema="members")

    def _test_show_schema_image(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_schema,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_SCHEMA_IMAGE,
            bytes_body,
            schema="image")

    def _test_show_schema_images(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_schema,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_SCHEMA_IMAGE,
            bytes_body,
            schema="images")

    def _test_show_schema(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_schema,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_SCHEMA,
            bytes_body,
            schema="member")

    def test_show_schema_members_with_str_body(self):
        self._test_show_schema_members()

    def test_show_schema_members_with_bytes_body(self):
        self._test_show_schema_members(bytes_body=True)

    def test_show_schema_image_with_str_body(self):
        self._test_show_schema_image()

    def test_show_schema_image_with_bytes_body(self):
        self._test_show_schema_image(bytes_body=True)

    def test_show_schema_images_with_str_body(self):
        self._test_show_schema_images()

    def test_show_schema_images_with_bytes_body(self):
        self._test_show_schema_images(bytes_body=True)

    def test_show_schema_with_str_body(self):
        self._test_show_schema()

    def test_show_schema_with_bytes_body(self):
        self._test_show_schema(bytes_body=True)
