# Copyright 2016 EasyStack.  All rights reserved.
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

from tempest.lib.services.image.v2 import namespace_properties_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNamespacePropertiesClient(base.BaseServiceTest):
    FAKE_CREATE_SHOW_NAMESPACE_PROPERTY = {
        "description": "property",
        "enum": ["xen", "qemu", "kvm", "lxc", "uml", "vmware", "hyperv"],
        "name": "OS::Glance::Image",
        "title": "Hypervisor Type",
        "type": "string"
    }

    FAKE_LIST_NAMESPACE_PROPERTY = {
        "properties": {
            "hw_disk_bus": {
                "description": "property.",
                "enum": ["scsi", "virtio", "uml", "xen", "ide", "usb"],
                "title": "Disk Bus",
                "type": "string"
            },
            "hw_machine_type": {
                "description": "desc.",
                "title": "Machine Type",
                "type": "string"
            },
            "hw_qemu_guest_agent": {
                "description": "desc.",
                "enum": [
                    "yes",
                    "no"
                ],
                "title": "QEMU Guest Agent",
                "type": "string"
            },
            "hw_rng_model": {
                "default": "virtio",
                "description": "desc",
                "title": "Random Number Generator Device",
                "type": "string"
            },
            "hw_scsi_model": {
                "default": "virtio-scsi",
                "description": "desc.",
                "title": "SCSI Model",
                "type": "string"
            },
            "hw_video_model": {
                "description": "The video image driver used.",
                "enum": [
                    "vga",
                    "cirrus",
                    "vmvga",
                    "xen",
                    "qxl"
                ],
                "title": "Video Model",
                "type": "string"
            },
            "hw_video_ram": {
                "description": "desc.",
                "title": "Max Video Ram",
                "type": "integer"
            },
            "hw_vif_model": {
                "description": "desc.",
                "enum": ["e1000",
                         "ne2k_pci",
                         "pcnet",
                         "rtl8139",
                         "virtio",
                         "e1000",
                         "e1000e",
                         "VirtualE1000",
                         "VirtualE1000e",
                         "VirtualPCNet32",
                         "VirtualSriovEthernetCard",
                         "VirtualVmxnet",
                         "netfront",
                         "ne2k_pci"
                         ],
                "title": "Virtual Network Interface",
                "type": "string"
            },
            "os_command_line": {
                "description": "desc.",
                "title": "Kernel Command Line",
                "type": "string"
            }
        }
    }

    FAKE_UPDATE_NAMESPACE_PROPERTY = {
        "description": "property",
        "enum": ["xen", "qemu", "kvm", "lxc", "uml", "vmware", "hyperv"],
        "name": "OS::Glance::Image",
        "title": "update Hypervisor Type",
        "type": "string"
    }

    def setUp(self):
        super(TestNamespacePropertiesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = namespace_properties_client.NamespacePropertiesClient(
            fake_auth, 'image', 'regionOne')

    def _test_create_namespace_property(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_namespace_property,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SHOW_NAMESPACE_PROPERTY,
            bytes_body, status=201,
            namespace="OS::Compute::Hypervisor",
            title="Hypervisor Type", name="OS::Glance::Image",
            type="string",
            enum=["xen", "qemu", "kvm", "lxc", "uml", "vmware", "hyperv"])

    def _test_list_namespace_property(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_namespace_properties,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_NAMESPACE_PROPERTY,
            bytes_body,
            namespace="OS::Compute::Hypervisor")

    def _test_show_namespace_property(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_namespace_properties,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CREATE_SHOW_NAMESPACE_PROPERTY,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            property_name="OS::Glance::Image")

    def _test_update_namespace_property(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_namespace_properties,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_NAMESPACE_PROPERTY,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            property_name="OS::Glance::Image",
            title="update Hypervisor Type", type="string",
            enum=["xen", "qemu", "kvm", "lxc", "uml", "vmware", "hyperv"],
            name="OS::Glance::Image")

    def test_create_namespace_property_with_str_body(self):
        self._test_create_namespace_property()

    def test_create_namespace_property_with_bytes_body(self):
        self._test_create_namespace_property(bytes_body=True)

    def test_list_namespace_property_with_str_body(self):
        self._test_list_namespace_property()

    def test_list_namespace_property_with_bytes_body(self):
        self._test_list_namespace_property(bytes_body=True)

    def test_show_namespace_property_with_str_body(self):
        self._test_show_namespace_property()

    def test_show_namespace_property_with_bytes_body(self):
        self._test_show_namespace_property(bytes_body=True)

    def test_update_namespace_property_with_str_body(self):
        self._test_update_namespace_property()

    def test_update_namespace_property_with_bytes_body(self):
        self._test_update_namespace_property(bytes_body=True)

    def test_delete_namespace(self):
        self.check_service_client_function(
            self.client.delete_namespace_property,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, namespace="OS::Compute::Hypervisor",
            property_name="OS::Glance::Image", status=204)
