# Copyright 2018 AT&T Corporation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures

from oslo_serialization import jsonutils as json
from tempest import clients
from tempest.cmd import cleanup_service
from tempest import config
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_credentials
from tempest.tests.lib import fake_http


class TestBaseService(base.TestCase):

    def test_base_service_init(self):
        kwargs = {'data': {'data': 'test'},
                  'is_dry_run': False,
                  'saved_state_json': {'saved': 'data'},
                  'is_preserve': False,
                  'is_save_state': True,
                  'tenant_id': 'project_id'}
        base = cleanup_service.BaseService(kwargs)
        self.assertEqual(base.data, kwargs['data'])
        self.assertFalse(base.is_dry_run)
        self.assertEqual(base.saved_state_json, kwargs['saved_state_json'])
        self.assertFalse(base.is_preserve)
        self.assertTrue(base.is_save_state)
        self.assertEqual(base.tenant_filter['project_id'], kwargs['tenant_id'])


class MockFunctionsBase(base.TestCase):

    def _create_response(self, body, status, headers):
        if status:
            if body:
                body = json.dumps(body)
            resp = fake_http.fake_http_response(headers, status=status), body
            return resp
        else:
            return body

    def _create_fixtures(self, fixtures_to_make):
        mocked_fixtures = []
        for fixture in fixtures_to_make:
            func, body, status = fixture
            mocked_response = self._create_response(body, status, None)
            if mocked_response == 'error':
                mocked_func = self.useFixture(fixtures.MockPatch(
                    func, side_effect=Exception("error")))
            else:
                mocked_func = self.useFixture(fixtures.MockPatch(
                    func, return_value=mocked_response))
            mocked_fixtures.append(mocked_func)
        return mocked_fixtures

    def run_function_with_mocks(self, function_to_run, functions_to_mock):
        """Mock a service client function for testing.

        :param function_to_run: The service client function to call.
        :param functions_to_mock: a list of tuples containing the function
               to mock, the response body, and the response status.
               EX:
               ('tempest.lib.common.rest_client.RestClient.get',
                {'users': ['']},
                200)
        """
        mocked_fixtures = self._create_fixtures(functions_to_mock)
        func_return = function_to_run()
        return func_return, mocked_fixtures


class BaseCmdServiceTests(MockFunctionsBase):

    def setUp(self):
        super(BaseCmdServiceTests, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.useFixture(fixtures.MockPatch(
            'tempest.cmd.cleanup_service._get_network_id',
            return_value=''))
        cleanup_service.init_conf()
        self.conf_values = {"flavors": cleanup_service.CONF_FLAVORS[0],
                            "images": cleanup_service.CONF_IMAGES[0],
                            "projects": cleanup_service.CONF_PROJECTS[0],
                            "users": cleanup_service.CONF_USERS[0],
                            "networks": cleanup_service.CONF_PUB_NETWORK,
                            "security_groups":
                                cleanup_service.CONF_PROJECTS[0],
                            "ports": cleanup_service.CONF_PUB_NETWORK,
                            "routers": cleanup_service.CONF_PUB_ROUTER,
                            "subnetpools": cleanup_service.CONF_PROJECTS[0],
                            }

    saved_state = {
        # Static list to ensure global service saved items are not deleted
        "users": {u'32rwef64245tgr20121qw324bgg': u'Lightning'},
        "flavors": {u'42': u'm1.tiny'},
        "images": {u'34yhwr-4t3q': u'stratus-0.3.2-x86_64-disk'},
        "roles": {u'3efrt74r45hn': u'president'},
        "projects": {u'f38ohgp93jj032': u'manhattan'},
        "domains": {u'default': u'Default'},
        # Static list to ensure project service saved items are not deleted
        "snapshots": {u'1ad4c789-7e8w-4dwg-afc5': u'saved-snapshot'},
        "servers": {u'7a6d4v7w-36ds-4216': u'saved-server'},
        "server_groups": {u'as6d5f7g-46ca-475e': u'saved-server-group'},
        "keypairs": {u'saved-key-pair': {
            u'fingerprint': u'7e:eb:ab:24',
            u'name': u'saved-key-pair'
        }},
        "volumes": {u'aa77asdf-1234': u'saved-volume'},
        "networks": {u'6722fc13-4319': {
            u'id': u'6722fc13-4319',
            u'name': u'saved-network'
        }},
        "floatingips": {u'9e82d248-408a': {
            u'id': u'9e82d248-408a',
            u'status': u'ACTIVE'
        }},
        "routers": {u'4s5w34hj-id44': u'saved-router'},
        "metering_label_rules": {u'93a973ce-4dc5': {
            u'direction': u'ingress',
            u'id': u'93a973ce-4dc5'
        }},
        "metering_labels": {u'723b346ce866-4c7q': u'saved-label'},
        "ports": {u'aa74aa4v-741a': u'saved-port'},
        "security_groups": {u'7q844add-3697': u'saved-sec-group'},
        "subnets": {u'55ttda4a-2584': u'saved-subnet'},
        "subnetpools": {u'8acf64c1-43fc': u'saved-subnet-pool'}
    }
    # Mocked methods
    get_method = 'tempest.lib.common.rest_client.RestClient.get'
    delete_method = 'tempest.lib.common.rest_client.RestClient.delete'
    log_method = 'tempest.cmd.cleanup_service.LOG.exception'
    # Override parameters
    service_class = 'BaseService'
    response = None
    service_name = 'default'

    def _create_cmd_service(self, service_type, is_save_state=False,
                            is_preserve=False, is_dry_run=False):
        creds = fake_credentials.FakeKeystoneV3Credentials()
        os = clients.Manager(creds)
        return getattr(cleanup_service, service_type)(
            os,
            is_save_state=is_save_state,
            is_preserve=is_preserve,
            is_dry_run=is_dry_run,
            data={},
            saved_state_json=self.saved_state
            )

    def _test_delete(self, mocked_fixture_tuple_list, fail=False):
        serv = self._create_cmd_service(self.service_class)
        resp, fixtures = self.run_function_with_mocks(
            serv.run,
            mocked_fixture_tuple_list,
        )
        for fixture in fixtures:
            if fixture.mock.return_value == 'validate':
                fixture.mock.assert_called()
            elif fail is False and fixture.mock.return_value == 'exception':
                fixture.mock.assert_not_called()
            elif self.service_name in self.saved_state.keys():
                fixture.mock.assert_called_once()
                for key in self.saved_state[self.service_name].keys():
                    self.assertNotIn(key, fixture.mock.call_args[0][0])
            else:
                fixture.mock.assert_called_once()
        self.assertFalse(serv.data)

    def _test_dry_run_true(self, mocked_fixture_tuple_list):
        serv = self._create_cmd_service(self.service_class, is_dry_run=True)
        _, fixtures = self.run_function_with_mocks(
            serv.run,
            mocked_fixture_tuple_list
        )
        for fixture in fixtures:
            if fixture.mock.return_value == 'delete':
                fixture.mock.assert_not_called()
            elif self.service_name in self.saved_state.keys():
                fixture.mock.assert_called_once()
                for key in self.saved_state[self.service_name].keys():
                    self.assertNotIn(key, fixture.mock.call_args[0][0])
            else:
                fixture.mock.assert_called_once()

    def _test_saved_state_true(self, mocked_fixture_tuple_list):
        serv = self._create_cmd_service(self.service_class, is_save_state=True)
        _, fixtures = self.run_function_with_mocks(
            serv.run,
            mocked_fixture_tuple_list
        )
        for item in self.response[self.service_name]:
            self.assertIn(item['id'],
                          serv.data[self.service_name])
        for fixture in fixtures:
            fixture.mock.assert_called_once()

    def _test_is_preserve_true(self, mocked_fixture_tuple_list):
        serv = self._create_cmd_service(self.service_class, is_preserve=True)
        resp, fixtures = self.run_function_with_mocks(
            serv.list,
            mocked_fixture_tuple_list
        )
        for fixture in fixtures:
            fixture.mock.assert_called_once()
        self.assertIn(resp[0], self.response[self.service_name])
        for rsp in resp:
            self.assertNotIn(rsp['id'], self.conf_values.values())
            self.assertNotIn(rsp['name'], self.conf_values.values())


class TestSnapshotService(BaseCmdServiceTests):

    service_class = 'SnapshotService'
    service_name = 'snapshots'
    response = {
        "snapshots": [
            {
                "status": "available",
                "metadata": {
                    "name": "test"
                },
                "name": "test-volume-snapshot",
                "user_id": "40c2102f4a554b848d96b14f3eec39ed",
                "volume_id": "173f7b48-c4c1-4e70-9acc-086b39073506",
                "created_at": "2015-11-29T02:25:51.000000",
                "size": 1,
                "updated_at": "2015-11-20T05:36:40.000000",
                "os-extended-snapshot-attributes:progress": "100%",
                "id": "b1323cda-8e4b-41c1-afc5-2fc791809c8c",
                "description": "volume snapshot"
            },
            {
                "status": "available",
                "name": "saved-snapshot",
                "id": "1ad4c789-7e8w-4dwg-afc5",
                "description": "snapshot in saved state"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 202),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestServerService(BaseCmdServiceTests):

    service_class = 'ServerService'
    service_name = 'servers'
    response = {
        "servers": [
            {
                "id": "22c91117-08de-4894-9aa9-6ef382400985",
                "links": [
                    {
                        "href": "http://openstack.example.com/v2/6f70-6ef0985",
                        "rel": "self"
                    },
                    {
                        "href": "http://openstack.example.com/6f70656e7-6ef35",
                        "rel": "bookmark"
                    }
                ],
                "name": "new-server-test"
            },
            {
                "id": "7a6d4v7w-36ds-4216",
                "links": [
                    {
                        "href": "http://openstack.example.com/v2/6f70-6ef0985",
                        "rel": "self"
                    },
                    {
                        "href": "http://openstack.example.com/6f70656e7-6ef35",
                        "rel": "bookmark"
                    }
                ],
                "name": "saved-server"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestServerGroupService(BaseCmdServiceTests):

    service_class = 'ServerGroupService'
    service_name = 'server_groups'
    validate_response = ('tempest.lib.services.compute.server_groups_client'
                         '.ServerGroupsClient.validate_response')

    response = {
        "server_groups": [
            {
                "id": "616fb98f-46ca-475e-917e-2563e5a8cd19",
                "name": "test",
                "policy": "anti-affinity",
                "rules": {"max_server_per_host": 3},
                "members": [],
                "project_id": "6f70656e737461636b20342065766572",
                "user_id": "fake"
            },
            {
                "id": "as6d5f7g-46ca-475e",
                "name": "saved-server-group"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.validate_response, 'validate', None),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.validate_response, 'validate', None),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.validate_response, 'validate', None),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200),
                                     (self.validate_response, 'validate', None)
                                     ])


class TestKeyPairService(BaseCmdServiceTests):

    service_class = 'KeyPairService'
    service_name = 'keypairs'
    validate_response = ('tempest.lib.services.compute.keypairs_client'
                         '.KeyPairsClient.validate_response')
    response = {
        "keypairs": [
            {
                "keypair": {
                    "fingerprint": "7e:eb:ab:24:ba:d1:e1:88:ae:9a:fb:66:53:bd",
                    "name": "keypair-5d935425-31d5-48a7-a0f1-e76e9813f2c3",
                    "type": "ssh",
                    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCkF\n"
                }
            },
            {
                "keypair": {
                    "fingerprint": "7e:eb:ab:24",
                    "name": "saved-key-pair"
                }
            }
        ]
    }

    def _test_saved_state_true(self, mocked_fixture_tuple_list):
        serv = self._create_cmd_service(self.service_class, is_save_state=True)
        _, fixtures = self.run_function_with_mocks(
            serv.run,
            mocked_fixture_tuple_list
        )
        for item in self.response[self.service_name]:
            self.assertTrue(item['keypair']['name'],
                            serv.data[self.service_name])
        for fixture in fixtures:
            fixture.mock.assert_called_once()

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.validate_response, 'validate', None),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.validate_response, 'validate', None),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.validate_response, 'validate', None),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([
            (self.get_method, self.response, 200),
            (self.validate_response, 'validate', None)
        ])


class TestVolumeService(BaseCmdServiceTests):

    service_class = 'VolumeService'
    service_name = 'volumes'
    response = {
        "volumes": [
            {
                "id": "efa54464-8fab-47cd-a05a-be3e6b396188",
                "links": [
                    {
                        "href": "http://127.0.0.1:37097/v3/89af/volumes/efa54",
                        "rel": "self"
                    },
                    {
                        "href": "http://127.0.0.1:37097/89af/volumes/efa54464",
                        "rel": "bookmark"
                    }
                ],
                "name": "volume-name"
            },
            {
                "id": "aa77asdf-1234",
                "name": "saved-volume"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 202),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


# Begin network service classes
class TestNetworkService(BaseCmdServiceTests):

    service_class = 'NetworkService'
    service_name = 'networks'
    response = {
        "networks": [
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2016-03-08T20:19:41",
                "dns_domain": "my-domain.org.",
                "id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
                "l2_adjacency": False,
                "mtu": 1500,
                "name": "net1",
                "port_security_enabled": True,
                "project_id": "4fd44f30292945e481c7b8a0c8908869",
                "qos_policy_id": "6a8454ade84346f59e8d40665f878b2e",
                "revision_number": 1,
                "router:external": False,
                "shared": False,
                "status": "ACTIVE",
                "subnets": [
                    "54d6f61d-db07-451c-9ab3-b9609b6b6f0b"
                ],
                "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
                "updated_at": "2016-03-08T20:19:41",
                "vlan_transparent": True,
                "description": "",
                "is_default": False
            },
            {
                "id": "6722fc13-4319",
                "name": "saved-network"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['networks'].append(
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2017-03-08T20:19:41",
                "dns_domain": "my-domain.org.",
                "id": cleanup_service.CONF_PUB_NETWORK,
                "name": "net2",
                "port_security_enabled": True,
                "project_id": "4fd44f30292945e481c7b8a0c8908869",
                "qos_policy_id": "6a8454ade84346f59e8d40665f878b2e",
                "revision_number": 1,
                "status": "ACTIVE",
                "subnets": [
                    "54d6f61d-db07-451c-9ab3-b9609b6b6f0b"
                ],
                "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
                "updated_at": "2018-03-08T20:19:41",
                "vlan_transparent": True,
                "is_default": False
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestNetworkFloatingIpService(BaseCmdServiceTests):

    service_class = 'NetworkFloatingIpService'
    service_name = 'floatingips'
    response = {
        "floatingips": [
            {
                "router_id": "d23abc8d-2991-4a55-ba98-2aaea84cc72f",
                "description": "for test",
                "dns_domain": "my-domain.org.",
                "dns_name": "myfip",
                "created_at": "2016-12-21T10:55:50Z",
                "updated_at": "2016-12-21T10:55:53Z",
                "revision_number": 1,
                "project_id": "4969c491a3c74ee4af974e6d800c62de",
                "tenant_id": "4969c491a3c74ee4af974e6d800c62de",
                "floating_network_id": "376da547-b977-4cfe-9cba-275c80debf57",
                "fixed_ip_address": "10.0.0.3",
                "floating_ip_address": "172.24.4.228",
                "port_id": "ce705c24-c1ef-408a-bda3-7bbd946164ab",
                "id": "2f245a7b-796b-4f26-9cf9-9e82d248fda7",
                "status": "ACTIVE",
                "port_details": {
                    "status": "ACTIVE",
                    "name": "",
                    "admin_state_up": True,
                    "network_id": "02dd8479-ef26-4398-a102-d19d0a7b3a1f",
                    "device_owner": "compute:nova",
                    "mac_address": "fa:16:3e:b1:3b:30",
                    "device_id": "8e3941b4-a6e9-499f-a1ac-2a4662025cba"
                },
                "tags": ["tag1,tag2"],
                "port_forwardings": []
            },
            {
                "id": "9e82d248-408a",
                "status": "ACTIVE"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestNetworkRouterService(BaseCmdServiceTests):

    service_class = 'NetworkRouterService'
    service_name = 'routers'
    validate_response = ('tempest.lib.services.network.routers_client'
                         '.RoutersClient.validate_response')
    response = {
        "routers": [
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2018-03-19T19:17:04Z",
                "description": "",
                "distributed": False,
                "external_gateway_info": {
                    "enable_snat": True,
                    "external_fixed_ips": [
                        {
                            "ip_address": "172.24.4.3",
                            "subnet_id": "b930d7f6-ceb7-40a0-8b81-a425dd994ccf"
                        },
                        {
                            "ip_address": "2001:db8::c",
                            "subnet_id": "0c56df5d-ace5-46c8-8f4c-45fa4e334d18"
                        }
                    ],
                    "network_id": "ae34051f-aa6c-4c75-abf5-50dc9ac99ef3"
                },
                "flavor_id": "f7b14d9a-b0dc-4fbe-bb14-a0f4970a69e0",
                "ha": False,
                "id": "915a14a6-867b-4af7-83d1-70efceb146f9",
                "name": "router2",
                "revision_number": 1,
                "routes": [
                    {
                        "destination": "179.24.1.0/24",
                        "nexthop": "172.24.3.99"
                    }
                ],
                "status": "ACTIVE",
                "updated_at": "2018-03-19T19:17:22Z",
                "project_id": "0bd18306d801447bb457a46252d82d13",
                "tenant_id": "0bd18306d801447bb457a46252d82d13",
                "tags": ["tag1,tag2"]
            },
            {
                "id": "4s5w34hj-id44",
                "name": "saved-router"
            }
        ],
        # "ports" key is added to the response in order to simplify unit
        # testing - it's because NetworkRouterService's delete method lists
        # ports before deleting any router
        "ports": []
    }

    def _test_delete(self, mocked_fixture_tuple_list, fail=False):
        serv = self._create_cmd_service(self.service_class)
        resp, fixtures = self.run_function_with_mocks(
            serv.run,
            mocked_fixture_tuple_list,
        )
        for fixture in fixtures:
            if fail is False and fixture.mock.return_value == 'exception':
                fixture.mock.assert_not_called()
            elif self.service_name in self.saved_state.keys():
                fixture.mock.assert_called()
                for key in self.saved_state[self.service_name].keys():
                    self.assertNotIn(key, fixture.mock.call_args[0][0])
        self.assertFalse(serv.data)

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['routers'].append(
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2018-03-19T19:17:04Z",
                "id": cleanup_service.CONF_PUB_ROUTER,
                "name": "router-preserve",
                "status": "ACTIVE",
                "updated_at": "2018-03-19T19:17:22Z",
                "project_id": "0bd18306d801447bb457a46252d82d13",
                "tenant_id": "0bd18306d801447bb457a46252d82d13",
                "tags": ["tag1,tag2"]
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestNetworkMeteringLabelRuleService(BaseCmdServiceTests):

    service_class = 'NetworkMeteringLabelRuleService'
    service_name = 'metering_label_rules'
    response = {
        "metering_label_rules": [
            {
                "remote_ip_prefix": "20.0.0.0/24",
                "direction": "ingress",
                "metering_label_id": "e131d186-b02d-4c0b-83d5-0c0725c4f812",
                "id": "9536641a-7d14-4dc5-afaf-93a973ce0eb8",
                "excluded": False
            },
            {
                "direction": "ingress",
                "id": "93a973ce-4dc5"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestNetworkMeteringLabelService(BaseCmdServiceTests):

    service_class = 'NetworkMeteringLabelService'
    service_name = 'metering_labels'
    response = {
        "metering_labels": [
            {
                "project_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "tenant_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "description": "label1 description",
                "name": "label1",
                "id": "a6700594-5b7a-4105-8bfe-723b346ce866",
                "shared": False
            },
            {
                "name": "saved-label",
                "id": "723b346ce866-4c7q",
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestNetworkPortService(BaseCmdServiceTests):

    service_class = 'NetworkPortService'
    service_name = 'ports'
    response = {
        "ports": [
            {
                "admin_state_up": True,
                "allowed_address_pairs": [],
                "created_at": "2016-03-08T20:19:41",
                "description": "",
                "device_id": "9ae135f4-b6e0-4dad-9e91-3c223e385824",
                "device_owner": "",
                "dns_assignment": {
                    "hostname": "myport",
                    "ip_address": "172.24.4.2",
                    "fqdn": "myport.my-domain.org"
                },
                "dns_domain": "my-domain.org.",
                "dns_name": "myport",
                "extra_dhcp_opts": [
                    {
                        "opt_value": "pxelinux.0",
                        "ip_version": 4,
                        "opt_name": "bootfile-name"
                    }
                ],
                "fixed_ips": [
                    {
                        "ip_address": "172.24.4.2",
                        "subnet_id": "008ba151-0b8c-4a67-98b5-0d2b87666062"
                    }
                ],
                "id": "d80b1a3b-4fc1-49f3-952e-1e2ab7081d8b",
                "ip_allocation": "immediate",
                "mac_address": "fa:16:3e:58:42:ed",
                "name": "test_port",
                "network_id": "70c1db1f-b701-45bd-96e0-a313ee3430b3",
                "project_id": "",
                "revision_number": 1,
                "security_groups": [],
                "status": "ACTIVE",
                "tags": ["tag1,tag2"],
                "tenant_id": "",
                "updated_at": "2016-03-08T20:19:41",
                "qos_policy_id": "29d5e02e-d5ab-4929-bee4-4a9fc12e22ae",
                "port_security_enabled": False
            },
            {
                "id": "aa74aa4v-741a",
                "name": "saved-port",
                "device_owner": ""
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['ports'].append(
            {
                "created_at": "2018-03-08T20:19:41",
                "description": "",
                "device_id": "9ae135f4-b6e0-4dad-9e91-3c223e385824",
                "device_owner": "compute:router_gateway",
                "id": "d80b1a3b-4fc1-49f3-952e-1fdy1ws542",
                "ip_allocation": "immediate",
                "mac_address": "fa:16:3e:58:42:ed",
                "name": "preserve_port",
                "network_id": cleanup_service.CONF_PUB_NETWORK,
                "project_id": "",
                "security_groups": [],
                "status": "ACTIVE",
                "tags": ["tag1,tag2"],
                "tenant_id": "",
                "updated_at": "2018-03-08T20:19:41",
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestNetworkSecGroupService(BaseCmdServiceTests):

    service_class = 'NetworkSecGroupService'
    service_name = 'security_groups'
    response = {
        "security_groups": [
            {
                "description": "default",
                "id": "85cc3048-abc3-43cc-89b3-377341426ac5",
                "name": "test",
                "security_group_rules": [
                    {
                        "direction": "egress",
                        "ethertype": "IPv6",
                        "id": "3c0e45ff-adaf-4124-b083-bf390e5482ff",
                        "security_group_id": "85cc3048-abc3-43cc-89b3-3773414",
                        "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "revision_number": 1,
                        "tags": ["tag1,tag2"],
                        "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "created_at": "2018-03-19T19:16:56Z",
                        "updated_at": "2018-03-19T19:16:56Z",
                        "description": ""
                    }
                ]
            },
            {
                "id": "7q844add-3697",
                "name": "saved-sec-group"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['security_groups'].append(
            {
                "description": "default",
                "id": "85cc3048-abc3-43cc-89b3-377341426ac5",
                "name": "test",
                "security_group_rules": [
                    {
                        "direction": "egress",
                        "ethertype": "IPv6",
                        "id": "3c0e45ff-adaf-4124-b083-bf390e5482ff",
                        "security_group_id": "85cc3048-abc3-43cc-89b3-3773414",
                        "project_id": cleanup_service.CONF_PROJECTS[0],
                        "revision_number": 1,
                        "tags": ["tag1,tag2"],
                        "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "created_at": "2018-03-19T19:16:56Z",
                        "updated_at": "2018-03-19T19:16:56Z",
                        "description": ""
                    }
                ]
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestNetworkSubnetService(BaseCmdServiceTests):

    service_class = 'NetworkSubnetService'
    service_name = 'subnets'
    response = {
        "subnets": [
            {
                "name": "private-subnet",
                "enable_dhcp": True,
                "network_id": "db193ab3-96e3-4cb3-8fc5-05f4296d0324",
                "project_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "tenant_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "dns_nameservers": [],
                "allocation_pools": [
                    {
                        "start": "10.0.0.2",
                        "end": "10.0.0.254"
                    }
                ],
                "host_routes": [],
                "ip_version": 4,
                "gateway_ip": "10.0.0.1",
                "cidr": "10.0.0.0/24",
                "id": "08eae331-0402-425a-923c-34f7cfe39c1b",
                "created_at": "2016-10-10T14:35:34Z",
                "revision_number": 2,
                "service_types": [],
                "tags": ["tag1,tag2"],
                "updated_at": "2016-10-10T14:35:34Z"
            },
            {
                "id": "55ttda4a-2584",
                "name": "saved-subnet"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['subnets'].append(
            {
                "name": "public-subnet",
                "network_id": cleanup_service.CONF_PUB_NETWORK,
                "project_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "tenant_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "ip_version": 4,
                "gateway_ip": "10.0.0.1",
                "cidr": "10.0.0.0/24",
                "id": "08eae331-0402-425a-923c-34f7cfe39c1b",
                "created_at": "2018-10-10T14:35:34Z",
                "service_types": [],
                "tags": ["tag1,tag2"],
                "updated_at": "2018-10-10T14:35:34Z"
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestNetworkSubnetPoolsService(BaseCmdServiceTests):

    service_class = 'NetworkSubnetPoolsService'
    service_name = 'subnetpools'
    response = {
        "subnetpools": [
            {
                "min_prefixlen": "64",
                "default_prefixlen": "64",
                "id": "03f761e6-eee0-43fc-a921-8acf64c14988",
                "max_prefixlen": "64",
                "name": "my-subnet-pool-ipv6",
                "is_default": False,
                "project_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "tenant_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "prefixes": [
                    "2001:db8:0:2::/64",
                    "2001:db8::/63"
                ],
                "ip_version": 6,
                "shared": False,
                "description": "",
                "created_at": "2016-03-08T20:19:41",
                "updated_at": "2016-03-08T20:19:41",
                "revision_number": 2,
                "tags": ["tag1,tag2"]
            },
            {
                "id": "8acf64c1-43fc",
                "name": "saved-subnet-pool"
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['subnetpools'].append(
            {
                "min_prefixlen": "64",
                "default_prefixlen": "64",
                "id": "9acf64c1-43fc",
                "name": "preserve-pool",
                "project_id": cleanup_service.CONF_PROJECTS[0],
                "created_at": "2016-03-08T20:19:41",
                "updated_at": "2016-03-08T20:19:41"
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


# begin global services
class TestDomainService(BaseCmdServiceTests):

    service_class = 'DomainService'
    service_name = 'domains'
    response = {
        "domains": [
            {
                "description": "Destroy all humans",
                "enabled": True,
                "id": "5a75994a3",
                "links": {
                    "self": "http://example.com/identity/v3/domains/5a75994a3"
                },
                "name": "Sky_net"
            },
            {
                "description": "Owns users and tenants on Identity API",
                "enabled": False,
                "id": "default",
                "links": {
                    "self": "http://example.com/identity/v3/domains/default"
                },
                "name": "Default"
            }
        ]
    }

    mock_update = ("tempest.lib.services.identity.v3."
                   "domains_client.DomainsClient.update_domain")

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None),
                       (self.mock_update, 'update', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None),
                       (self.mock_update, 'update', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestProjectsService(BaseCmdServiceTests):

    service_class = 'ProjectService'
    service_name = 'projects'
    response = {
        "projects": [
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "f38ohgp93jj032",
                "links": {
                    "self": "http://example.com/identity/v3/projects"
                            "/f38ohgp93jj032"
                },
                "name": "manhattan",
                "parent_id": None
            },
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "098f89d3292ri4jf4",
                "links": {
                    "self": "http://example.com/identity/v3/projects"
                            "/098f89d3292ri4jf4"
                },
                "name": "Apollo",
                "parent_id": None
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['projects'].append(
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "r343q98h09f3092",
                "links": {
                    "self": "http://example.com/identity/v3/projects"
                            "/r343q98h09f3092"
                },
                "name": cleanup_service.CONF_PROJECTS[0],
                "parent_id": None
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestImagesService(BaseCmdServiceTests):

    service_class = 'ImageService'
    service_name = 'images'
    response = {
        "images": [
            {
                "status": "ACTIVE",
                "name": "stratus-0.3.2-x86_64-disk",
                "id": "34yhwr-4t3q",
                "updated": "2014-11-03T16:40:10Z",
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/images/"
                    "34yhwr-4t3q",
                    "rel": "self"}],
                "created": "2014-10-30T08:23:39Z",
                "minDisk": 0,
                "minRam": 0,
                "progress": 0,
                "metadata": {},
            },
            {
                "status": "ACTIVE",
                "name": "cirros-0.3.2-x86_64-disk",
                "id": "1bea47ed-f6a9",
                "updated": "2014-11-03T16:40:10Z",
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/images/"
                    "1bea47ed-f6a9",
                    "rel": "self"}],
                "created": "2014-10-30T08:23:39Z",
                "minDisk": 0,
                "minRam": 0,
                "progress": 0,
                "metadata": {},
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['images'].append(
            {
                "status": "ACTIVE",
                "name": "cirros-0.3.2-x86_64-disk",
                "id": cleanup_service.CONF_IMAGES[0],
                "updated": "2014-11-03T16:40:10Z",
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/images/"
                    "None",
                    "rel": "self"}],
                "created": "2014-10-30T08:23:39Z",
                "minDisk": 0,
                "minRam": 0,
                "progress": 0,
                "metadata": {},
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestFlavorService(BaseCmdServiceTests):

    service_class = 'FlavorService'
    service_name = 'flavors'
    response = {
        "flavors": [
            {
                "disk": 1,
                "id": "42",
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/flavors/1",
                    "rel": "self"}, {
                    "href": "http://openstack.ex.com/openstack/flavors/1",
                    "rel": "bookmark"}],
                "name": "m1.tiny",
                "ram": 512,
                "swap": 1,
                "vcpus": 1
            },
            {
                "disk": 2,
                "id": "13",
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/flavors/2",
                    "rel": "self"}, {
                    "href": "http://openstack.ex.com/openstack/flavors/2",
                    "rel": "bookmark"}],
                "name": "m1.tiny",
                "ram": 512,
                "swap": 1,
                "vcpus": 1
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 202),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['flavors'].append(
            {
                "disk": 3,
                "id": cleanup_service.CONF_FLAVORS[0],
                "links": [{
                    "href": "http://openstack.ex.com/v2/openstack/flavors/3",
                    "rel": "self"}, {
                    "href": "http://openstack.ex.com/openstack/flavors/3",
                    "rel": "bookmark"}],
                "name": "m1.tiny",
                "ram": 512,
                "swap": 1,
                "vcpus": 1
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])


class TestRoleService(BaseCmdServiceTests):

    service_class = 'RoleService'
    service_name = 'roles'
    response = {
        "roles": [
            {
                "domain_id": "FakeDomain",
                "id": "3efrt74r45hn",
                "name": "president",
                "links": {
                    "self": "http://ex.com/identity/v3/roles/3efrt74r45hn"
                }
            },
            {
                "domain_id": 'FakeDomain',
                "id": "39ruo5sdk040",
                "name": "vice-p",
                "links": {
                    "self": "http://ex.com/identity/v3/roles/39ruo5sdk040"
                }
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])


class TestUserService(BaseCmdServiceTests):

    service_class = 'UserService'
    service_name = 'users'
    response = {
        "users": [
            {
                "domain_id": "TempestDomain",
                "enabled": True,
                "id": "e812fb332456423fdv1b1320121qwe2",
                "links": {
                    "self": "http://example.com/identity/v3/users/"
                            "e812fb332456423fdv1b1320121qwe2",
                },
                "name": "Thunder",
                "password_expires_at": "3102-11-06T15:32:17.000000",
            },
            {
                "domain_id": "TempestDomain",
                "enabled": True,
                "id": "32rwef64245tgr20121qw324bgg",
                "links": {
                    "self": "http://example.com/identity/v3/users/"
                            "32rwef64245tgr20121qw324bgg",
                },
                "name": "Lightning",
                "password_expires_at": "1893-11-06T15:32:17.000000",
            }
        ]
    }

    def test_delete_fail(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, 'error', None),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock, fail=True)

    def test_delete_pass(self):
        delete_mock = [(self.get_method, self.response, 200),
                       (self.delete_method, None, 204),
                       (self.log_method, 'exception', None)]
        self._test_delete(delete_mock)

    def test_dry_run(self):
        dry_mock = [(self.get_method, self.response, 200),
                    (self.delete_method, "delete", None)]
        self._test_dry_run_true(dry_mock)

    def test_save_state(self):
        self._test_saved_state_true([(self.get_method, self.response, 200)])

    def test_preserve_list(self):
        self.response['users'].append(
            {
                "domain_id": "TempestDomain",
                "enabled": True,
                "id": "23ads5tg3rtrhe30121qwhyth",
                "links": {
                    "self": "http://example.com/identity/v3/users/"
                            "23ads5tg3rtrhe30121qwhyth",
                },
                "name": cleanup_service.CONF_USERS[0],
                "password_expires_at": "1893-11-06T15:32:17.000000",
            })
        self._test_is_preserve_true([(self.get_method, self.response, 200)])
