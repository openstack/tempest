#!/usr/bin/env python
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

import mock
from oslotest import mockpatch

from tempest.cmd import javelin
from tempest.lib import exceptions as lib_exc
from tempest.tests import base


class JavelinUnitTest(base.TestCase):

    def setUp(self):
        super(JavelinUnitTest, self).setUp()
        javelin.LOG = mock.MagicMock()
        self.fake_client = mock.MagicMock()
        self.fake_object = mock.MagicMock()

    def test_load_resources(self):
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True) as open_mock:
            with mock.patch('yaml.load', mock.MagicMock(),
                            create=True) as load_mock:
                javelin.load_resources(self.fake_object)
                load_mock.assert_called_once_with(open_mock(self.fake_object))

    def test_keystone_admin(self):
        self.useFixture(mockpatch.PatchObject(javelin, "OSClient"))
        javelin.OPTS = self.fake_object
        javelin.keystone_admin()
        javelin.OSClient.assert_called_once_with(
            self.fake_object.os_username,
            self.fake_object.os_password,
            self.fake_object.os_tenant_name)

    def test_client_for_user(self):
        fake_user = mock.MagicMock()
        javelin.USERS = {fake_user['name']: fake_user}
        self.useFixture(mockpatch.PatchObject(javelin, "OSClient"))
        javelin.client_for_user(fake_user['name'])
        javelin.OSClient.assert_called_once_with(
            fake_user['name'], fake_user['pass'], fake_user['tenant'])

    def test_client_for_non_existing_user(self):
        fake_non_existing_user = self.fake_object
        fake_user = mock.MagicMock()
        javelin.USERS = {fake_user['name']: fake_user}
        self.useFixture(mockpatch.PatchObject(javelin, "OSClient"))
        javelin.client_for_user(fake_non_existing_user['name'])
        self.assertFalse(javelin.OSClient.called)

    def test_attach_volumes(self):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        self.useFixture(mockpatch.PatchObject(
            javelin, "_get_volume_by_name",
            return_value=self.fake_object.volume))

        self.useFixture(mockpatch.PatchObject(
            javelin, "_get_server_by_name",
            return_value=self.fake_object.server))

        javelin.attach_volumes([self.fake_object])

        mocked_function = self.fake_client.volumes.attach_volume
        mocked_function.assert_called_once_with(
            self.fake_object.volume['id'],
            instance_uuid=self.fake_object.server['id'],
            mountpoint=self.fake_object['device'])


class TestCreateResources(JavelinUnitTest):
    def test_create_tenants(self):

        self.fake_client.tenants.list_tenants.return_value = {'tenants': []}
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=self.fake_client))

        javelin.create_tenants([self.fake_object['name']])

        mocked_function = self.fake_client.tenants.create_tenant
        mocked_function.assert_called_once_with(self.fake_object['name'])

    def test_create_duplicate_tenant(self):
        self.fake_client.tenants.list_tenants.return_value = {'tenants': [
            {'name': self.fake_object['name']}]}
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=self.fake_client))

        javelin.create_tenants([self.fake_object['name']])

        mocked_function = self.fake_client.tenants.create_tenant
        self.assertFalse(mocked_function.called)

    def test_create_users(self):
        self.useFixture(mockpatch.Patch(
                        'tempest.common.identity.get_tenant_by_name',
                        return_value=self.fake_object['tenant']))
        self.useFixture(mockpatch.Patch(
                        'tempest.common.identity.get_user_by_username',
                        side_effect=lib_exc.NotFound("user is not found")))
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=self.fake_client))

        javelin.create_users([self.fake_object])

        fake_tenant_id = self.fake_object['tenant']['id']
        fake_email = "%s@%s" % (self.fake_object['user'], fake_tenant_id)
        mocked_function = self.fake_client.users.create_user
        mocked_function.assert_called_once_with(self.fake_object['name'],
                                                self.fake_object['password'],
                                                fake_tenant_id,
                                                fake_email,
                                                enabled=True)

    def test_create_user_missing_tenant(self):
        self.useFixture(mockpatch.Patch(
                        'tempest.common.identity.get_tenant_by_name',
                        side_effect=lib_exc.NotFound("tenant is not found")))
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=self.fake_client))

        javelin.create_users([self.fake_object])

        mocked_function = self.fake_client.users.create_user
        self.assertFalse(mocked_function.called)

    def test_create_objects(self):

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_assign_swift_role"))
        self.useFixture(mockpatch.PatchObject(javelin, "_file_contents",
                        return_value=self.fake_object.content))

        javelin.create_objects([self.fake_object])

        mocked_function = self.fake_client.containers.create_container
        mocked_function.assert_called_once_with(self.fake_object['container'])
        mocked_function = self.fake_client.objects.create_object
        mocked_function.assert_called_once_with(self.fake_object['container'],
                                                self.fake_object['name'],
                                                self.fake_object.content)

    def test_create_images(self):
        self.fake_client.images.create_image.return_value = \
            self.fake_object['body']

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_get_image_by_name",
                                              return_value=[]))
        self.useFixture(mockpatch.PatchObject(javelin, "_resolve_image",
                                              return_value=(None, None)))

        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True) as open_mock:
            javelin.create_images([self.fake_object])

        mocked_function = self.fake_client.images.create_image
        mocked_function.assert_called_once_with(self.fake_object['name'],
                                                self.fake_object['format'],
                                                self.fake_object['format'])

        mocked_function = self.fake_client.images.store_image_file
        fake_image_id = self.fake_object['body'].get('id')
        mocked_function.assert_called_once_with(fake_image_id, open_mock())

    def test_create_networks(self):
        self.fake_client.networks.list_networks.return_value = {
            'networks': []}

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        javelin.create_networks([self.fake_object])

        mocked_function = self.fake_client.networks.create_network
        mocked_function.assert_called_once_with(name=self.fake_object['name'])

    def test_create_subnet(self):

        fake_network = self.fake_object['network']

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_get_resource_by_name",
                                              return_value=fake_network))

        fake_netaddr = mock.MagicMock()
        self.useFixture(mockpatch.PatchObject(javelin, "netaddr",
                                              return_value=fake_netaddr))
        fake_version = javelin.netaddr.IPNetwork().version

        javelin.create_subnets([self.fake_object])

        mocked_function = self.fake_client.networks.create_subnet
        mocked_function.assert_called_once_with(network_id=fake_network['id'],
                                                cidr=self.fake_object['range'],
                                                name=self.fake_object['name'],
                                                ip_version=fake_version)

    @mock.patch("tempest.common.waiters.wait_for_volume_status")
    def test_create_volumes(self, mock_wait_for_volume_status):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_get_volume_by_name",
                                              return_value=None))
        self.fake_client.volumes.create_volume.return_value = \
            self.fake_object.body

        javelin.create_volumes([self.fake_object])

        mocked_function = self.fake_client.volumes.create_volume
        mocked_function.assert_called_once_with(
            size=self.fake_object['gb'],
            display_name=self.fake_object['name'])
        mock_wait_for_volume_status.assert_called_once_with(
            self.fake_client.volumes, self.fake_object.body['volume']['id'],
            'available')

    @mock.patch("tempest.common.waiters.wait_for_volume_status")
    def test_create_volume_existing(self, mock_wait_for_volume_status):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_get_volume_by_name",
                                              return_value=self.fake_object))
        self.fake_client.volumes.create_volume.return_value = \
            self.fake_object.body

        javelin.create_volumes([self.fake_object])

        mocked_function = self.fake_client.volumes.create_volume
        self.assertFalse(mocked_function.called)
        self.assertFalse(mock_wait_for_volume_status.called)

    def test_create_router(self):

        self.fake_client.routers.list_routers.return_value = {'routers': []}
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        javelin.create_routers([self.fake_object])

        mocked_function = self.fake_client.networks.create_router
        mocked_function.assert_called_once_with(name=self.fake_object['name'])

    def test_create_router_existing(self):
        self.fake_client.routers.list_routers.return_value = {
            'routers': [self.fake_object]}
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        javelin.create_routers([self.fake_object])

        mocked_function = self.fake_client.networks.create_router
        self.assertFalse(mocked_function.called)

    def test_create_secgroup(self):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.fake_client.secgroups.list_security_groups.return_value = (
            {'security_groups': []})
        self.fake_client.secgroups.create_security_group.return_value = \
            {'security_group': {'id': self.fake_object['secgroup_id']}}

        javelin.create_secgroups([self.fake_object])

        mocked_function = self.fake_client.secgroups.create_security_group
        mocked_function.assert_called_once_with(
            name=self.fake_object['name'],
            description=self.fake_object['description'])


class TestDestroyResources(JavelinUnitTest):

    def test_destroy_tenants(self):

        fake_tenant = self.fake_object['tenant']
        fake_auth = self.fake_client
        self.useFixture(mockpatch.Patch(
                        'tempest.common.identity.get_tenant_by_name',
                        return_value=fake_tenant))
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=fake_auth))
        javelin.destroy_tenants([fake_tenant])

        mocked_function = fake_auth.tenants.delete_tenant
        mocked_function.assert_called_once_with(fake_tenant['id'])

    def test_destroy_users(self):

        fake_user = self.fake_object['user']
        fake_tenant = self.fake_object['tenant']

        fake_auth = self.fake_client
        fake_auth.tenants.list_tenants.return_value = \
            {'tenants': [fake_tenant]}
        fake_auth.users.list_users.return_value = {'users': [fake_user]}

        self.useFixture(mockpatch.Patch(
                        'tempest.common.identity.get_user_by_username',
                        return_value=fake_user))
        self.useFixture(mockpatch.PatchObject(javelin, "keystone_admin",
                                              return_value=fake_auth))

        javelin.destroy_users([fake_user])

        mocked_function = fake_auth.users.delete_user
        mocked_function.assert_called_once_with(fake_user['id'])

    def test_destroy_objects(self):

        self.fake_client.objects.delete_object.return_value = \
            {'status': "200"}, ""
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        javelin.destroy_objects([self.fake_object])

        mocked_function = self.fake_client.objects.delete_object
        mocked_function.asswert_called_once(self.fake_object['container'],
                                            self.fake_object['name'])

    def test_destroy_images(self):

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(javelin, "_get_image_by_name",
                        return_value=self.fake_object['image']))

        javelin.destroy_images([self.fake_object])

        mocked_function = self.fake_client.images.delete_image
        mocked_function.assert_called_once_with(
            self.fake_object['image']['id'])

    def test_destroy_networks(self):

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        self.useFixture(mockpatch.PatchObject(
            javelin, "_get_resource_by_name",
            return_value=self.fake_object['resource']))

        javelin.destroy_networks([self.fake_object])

        mocked_function = self.fake_client.networks.delete_network
        mocked_function.assert_called_once_with(
            self.fake_object['resource']['id'])

    def test_destroy_volumes(self):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        self.useFixture(mockpatch.PatchObject(
            javelin, "_get_volume_by_name",
            return_value=self.fake_object.volume))

        javelin.destroy_volumes([self.fake_object])

        mocked_function = self.fake_client.volumes.detach_volume
        mocked_function.assert_called_once_with(self.fake_object.volume['id'])
        mocked_function = self.fake_client.volumes.delete_volume
        mocked_function.assert_called_once_with(self.fake_object.volume['id'])

    def test_destroy_subnets(self):

        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        fake_subnet_id = self.fake_object['subnet_id']
        self.useFixture(mockpatch.PatchObject(javelin, "_get_resource_by_name",
                                              return_value={
                                                  'id': fake_subnet_id}))

        javelin.destroy_subnets([self.fake_object])

        mocked_function = self.fake_client.subnets.delete_subnet
        mocked_function.assert_called_once_with(fake_subnet_id)

    def test_destroy_routers(self):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))

        # this function is used on 2 different occasions in the code
        def _fake_get_resource_by_name(*args):
            if args[1] == "routers":
                return {"id": self.fake_object['router_id']}
            elif args[1] == "subnets":
                return {"id": self.fake_object['subnet_id']}
        javelin._get_resource_by_name = _fake_get_resource_by_name

        javelin.destroy_routers([self.fake_object])

        mocked_function = self.fake_client.routers.delete_router
        mocked_function.assert_called_once_with(
            self.fake_object['router_id'])

    def test_destroy_secgroup(self):
        self.useFixture(mockpatch.PatchObject(javelin, "client_for_user",
                                              return_value=self.fake_client))
        fake_secgroup = {'id': self.fake_object['id']}
        self.useFixture(mockpatch.PatchObject(javelin, "_get_resource_by_name",
                                              return_value=fake_secgroup))

        javelin.destroy_secgroups([self.fake_object])

        mocked_function = self.fake_client.secgroups.delete_security_group
        mocked_function.assert_called_once_with(self.fake_object['id'])
