# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

from tempest.lib.services.network import extensions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestExtensionsClient(base.BaseServiceTest):

    FAKE_EXTENSIONS = {
        "extensions": [
            {
                "updated": "2013-01-20T00:00:00-00:00",
                "name": "Neutron Service Type Management",
                "links": [],
                "alias": "service-type",
                "description": "API for retrieving service providers for"
                " Neutron advanced services"
            },
            {
                "updated": "2012-10-05T10:00:00-00:00",
                "name": "security-group",
                "links": [],
                "alias": "security-group",
                "description": "The security groups extension."
            },
            {
                "updated": "2013-02-07T10:00:00-00:00",
                "name": "L3 Agent Scheduler",
                "links": [],
                "alias": "l3_agent_scheduler",
                "description": "Schedule routers among l3 agents"
            },
            {
                "updated": "2013-02-07T10:00:00-00:00",
                "name": "Loadbalancer Agent Scheduler",
                "links": [],
                "alias": "lbaas_agent_scheduler",
                "description": "Schedule pools among lbaas agents"
            },
            {
                "updated": "2013-03-28T10:00:00-00:00",
                "name": "Neutron L3 Configurable external gateway mode",
                "links": [],
                "alias": "ext-gw-mode",
                "description":
                "Extension of the router abstraction for specifying whether"
                " SNAT should occur on the external gateway"
            },
            {
                "updated": "2014-02-03T10:00:00-00:00",
                "name": "Port Binding",
                "links": [],
                "alias": "binding",
                "description": "Expose port bindings of a virtual port to"
                " external application"
            },
            {
                "updated": "2012-09-07T10:00:00-00:00",
                "name": "Provider Network",
                "links": [],
                "alias": "provider",
                "description": "Expose mapping of virtual networks to"
                " physical networks"
            },
            {
                "updated": "2013-02-03T10:00:00-00:00",
                "name": "agent",
                "links": [],
                "alias": "agent",
                "description": "The agent management extension."
            },
            {
                "updated": "2012-07-29T10:00:00-00:00",
                "name": "Quota management support",
                "links": [],
                "alias": "quotas",
                "description": "Expose functions for quotas management per"
                " tenant"
            },
            {
                "updated": "2013-02-07T10:00:00-00:00",
                "name": "DHCP Agent Scheduler",
                "links": [],
                "alias": "dhcp_agent_scheduler",
                "description": "Schedule networks among dhcp agents"
            },
            {
                "updated": "2013-06-27T10:00:00-00:00",
                "name": "Multi Provider Network",
                "links": [],
                "alias": "multi-provider",
                "description": "Expose mapping of virtual networks to"
                " multiple physical networks"
            },
            {
                "updated": "2013-01-14T10:00:00-00:00",
                "name": "Neutron external network",
                "links": [],
                "alias": "external-net",
                "description": "Adds external network attribute to network"
                " resource."
            },
            {
                "updated": "2012-07-20T10:00:00-00:00",
                "name": "Neutron L3 Router",
                "links": [],
                "alias": "router",
                "description": "Router abstraction for basic L3 forwarding"
                " between L2 Neutron networks and access to external"
                " networks via a NAT gateway."
            },
            {
                "updated": "2013-07-23T10:00:00-00:00",
                "name": "Allowed Address Pairs",
                "links": [],
                "alias": "allowed-address-pairs",
                "description": "Provides allowed address pairs"
            },
            {
                "updated": "2013-03-17T12:00:00-00:00",
                "name": "Neutron Extra DHCP opts",
                "links": [],
                "alias": "extra_dhcp_opt",
                "description": "Extra options configuration for DHCP. For"
                " example PXE boot options to DHCP clients can be specified"
                " (e.g. tftp-server, server-ip-address, bootfile-name)"
            },
            {
                "updated": "2012-10-07T10:00:00-00:00",
                "name": "LoadBalancing service",
                "links": [],
                "alias": "lbaas",
                "description": "Extension for LoadBalancing service"
            },
            {
                "updated": "2013-02-01T10:00:00-00:00",
                "name": "Neutron Extra Route",
                "links": [],
                "alias": "extraroute",
                "description": "Extra routes configuration for L3 router"
            },
            {
                "updated": "2016-01-24T10:00:00-00:00",
                "name": "Neutron Port Data Plane Status",
                "links": [],
                "alias": "data-plane-status",
                "description": "Status of the underlying data plane."
            }
        ]
    }

    FAKE_EXTENSION_ALIAS = "service-type"

    def setUp(self):
        super(TestExtensionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.extensions_client = extensions_client.ExtensionsClient(
            fake_auth, "network", "regionOne")

    def _test_list_extensions(self, bytes_body=False):
        self.check_service_client_function(
            self.extensions_client.list_extensions,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_EXTENSIONS,
            bytes_body,
            200)

    def _test_show_extension(self, bytes_body=False):
        self.check_service_client_function(
            self.extensions_client.show_extension,
            "tempest.lib.common.rest_client.RestClient.get",
            {"extension": self.FAKE_EXTENSIONS["extensions"][0]},
            bytes_body,
            200,
            ext_alias=self.FAKE_EXTENSION_ALIAS)

    def test_list_extensions_with_str_body(self):
        self._test_list_extensions()

    def test_list_extensions_with_bytes_body(self):
        self._test_list_extensions(bytes_body=True)

    def test_show_extension_with_str_body(self):
        self._test_show_extension()

    def test_show_extension_with_bytes_body(self):
        self._test_show_extension(bytes_body=True)
