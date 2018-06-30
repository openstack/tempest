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
                            }

    # Static list to ensure global service saved items are not deleted
    saved_state = {"users": {u'32rwef64245tgr20121qw324bgg': u'Lightning'},
                   "flavors": {u'42': u'm1.tiny'},
                   "images": {u'34yhwr-4t3q': u'stratus-0.3.2-x86_64-disk'},
                   "roles": {u'3efrt74r45hn': u'president'},
                   "projects": {u'f38ohgp93jj032': u'manhattan'},
                   "domains": {u'default': u'Default'}
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
            if fail is False and fixture.mock.return_value == 'exception':
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
