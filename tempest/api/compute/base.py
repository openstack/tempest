# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import time

from tempest.api import compute
from tempest import clients
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test


LOG = logging.getLogger(__name__)


class BaseComputeTest(tempest.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    conclusion = compute.generic_setup_package()
    force_tenant_isolation = False

    @classmethod
    def setUpClass(cls):
        super(BaseComputeTest, cls).setUpClass()
        if not cls.config.service_available.nova:
            skip_msg = ("%s skipped as nova is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        os = cls.get_client_manager()

        cls.os = os
        cls.build_interval = cls.config.compute.build_interval
        cls.build_timeout = cls.config.compute.build_timeout
        cls.ssh_user = cls.config.compute.ssh_user
        cls.image_ref = cls.config.compute.image_ref
        cls.image_ref_alt = cls.config.compute.image_ref_alt
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.flavor_ref_alt = cls.config.compute.flavor_ref_alt
        cls.image_ssh_user = cls.config.compute.image_ssh_user
        cls.image_ssh_password = cls.config.compute.image_ssh_password
        cls.servers = []
        cls.images = []

    @classmethod
    def clear_servers(cls):
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except Exception:
                pass

        for server in cls.servers:
            try:
                cls.servers_client.wait_for_server_termination(server['id'])
            except Exception:
                pass

    @classmethod
    def clear_images(cls):
        for image_id in cls.images:
            try:
                cls.images_client.delete_image(image_id)
            except exceptions.NotFound:
                # The image may have already been deleted which is OK.
                pass
            except Exception as exc:
                LOG.info('Exception raised deleting image %s', image_id)
                LOG.exception(exc)
                pass

    @classmethod
    def tearDownClass(cls):
        cls.clear_images()
        cls.clear_servers()
        cls.clear_isolated_creds()
        super(BaseComputeTest, cls).tearDownClass()

    @classmethod
    def create_test_server(cls, **kwargs):
        """Wrapper utility that returns a test server."""
        name = data_utils.rand_name(cls.__name__ + "-instance")
        if 'name' in kwargs:
            name = kwargs.pop('name')
        flavor = kwargs.get('flavor', cls.flavor_ref)
        image_id = kwargs.get('image_id', cls.image_ref)

        resp, body = cls.servers_client.create_server(
            name, image_id, flavor, **kwargs)

        # handle the case of multiple servers
        servers = [body]
        if 'min_count' in kwargs or 'max_count' in kwargs:
            # Get servers created which name match with name param.
            r, b = cls.servers_client.list_servers()
            servers = [s for s in b['servers'] if s['name'].startswith(name)]

        cls.servers.extend(servers)

        if 'wait_until' in kwargs:
            for server in servers:
                cls.servers_client.wait_for_server_status(
                    server['id'], kwargs['wait_until'])

        return resp, body

    def wait_for(self, condition):
        """Repeatedly calls condition() until a timeout."""
        start_time = int(time.time())
        while True:
            try:
                condition()
            except Exception:
                pass
            else:
                return
            if int(time.time()) - start_time >= self.build_timeout:
                condition()
                return
            time.sleep(self.build_interval)


class BaseV2ComputeTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(BaseV2ComputeTest, cls).setUpClass()
        cls.servers_client = cls.os.servers_client
        cls.flavors_client = cls.os.flavors_client
        cls.images_client = cls.os.images_client
        cls.extensions_client = cls.os.extensions_client
        cls.floating_ips_client = cls.os.floating_ips_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_groups_client = cls.os.security_groups_client
        cls.quotas_client = cls.os.quotas_client
        cls.limits_client = cls.os.limits_client
        cls.volumes_extensions_client = cls.os.volumes_extensions_client
        cls.volumes_client = cls.os.volumes_client
        cls.interfaces_client = cls.os.interfaces_client
        cls.fixed_ips_client = cls.os.fixed_ips_client
        cls.availability_zone_client = cls.os.availability_zone_client
        cls.aggregates_client = cls.os.aggregates_client
        cls.services_client = cls.os.services_client
        cls.instance_usages_audit_log_client = \
            cls.os.instance_usages_audit_log_client
        cls.hypervisor_client = cls.os.hypervisor_client
        cls.servers_client_v3_auth = cls.os.servers_client_v3_auth
        cls.certificates_client = cls.os.certificates_client

    @classmethod
    def create_image_from_server(cls, server_id, **kwargs):
        """Wrapper utility that returns an image created from the server."""
        name = data_utils.rand_name(cls.__name__ + "-image")
        if 'name' in kwargs:
            name = kwargs.pop('name')

        resp, image = cls.images_client.create_image(
            server_id, name)
        image_id = data_utils.parse_image_id(resp['location'])
        cls.images.append(image_id)

        if 'wait_until' in kwargs:
            cls.images_client.wait_for_image_status(image_id,
                                                    kwargs['wait_until'])
            resp, image = cls.images_client.get_image(image_id)

            if kwargs['wait_until'] == 'ACTIVE':
                if kwargs.get('wait_for_server', True):
                    cls.servers_client.wait_for_server_status(server_id,
                                                              'ACTIVE')

        return resp, image

    @classmethod
    def rebuild_server(cls, server_id, **kwargs):
        # Destroy an existing server and creates a new one
        if server_id:
            try:
                cls.servers_client.delete_server(server_id)
                cls.servers_client.wait_for_server_termination(server_id)
            except Exception as exc:
                LOG.exception(exc)
                pass
        resp, server = cls.create_test_server(wait_until='ACTIVE', **kwargs)
        cls.password = server['adminPass']
        return server['id']


class BaseV2ComputeAdminTest(BaseV2ComputeTest):
    """Base test case class for Compute Admin V2 API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseV2ComputeAdminTest, cls).setUpClass()
        admin_username = cls.config.compute_admin.username
        admin_password = cls.config.compute_admin.password
        admin_tenant = cls.config.compute_admin.tenant_name
        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Compute Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        if (cls.config.compute.allow_tenant_isolation or
            cls.force_tenant_isolation is True):
            creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = creds
            cls.os_adm = clients.Manager(username=admin_username,
                                         password=admin_password,
                                         tenant_name=admin_tenant_name,
                                         interface=cls._interface)
        else:
            cls.os_adm = clients.ComputeAdminManager(interface=cls._interface)


class BaseV3ComputeTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(BaseV3ComputeTest, cls).setUpClass()
        if not cls.config.compute_feature_enabled.api_v3:
            cls.tearDownClass()
            skip_msg = ("%s skipped as nova v3 api is not available" %
                        cls.__name__)
            raise cls.skipException(skip_msg)

        cls.servers_client = cls.os.servers_v3_client
        cls.images_client = cls.os.image_client
        cls.services_client = cls.os.services_v3_client
        cls.extensions_client = cls.os.extensions_v3_client
        cls.availability_zone_client = cls.os.availability_zone_v3_client
        cls.interfaces_client = cls.os.interfaces_v3_client
        cls.hypervisor_client = cls.os.hypervisor_v3_client
        cls.tenant_usages_client = cls.os.tenant_usages_v3_client

    @classmethod
    def create_image_from_server(cls, server_id, **kwargs):
        """Wrapper utility that returns an image created from the server."""
        name = data_utils.rand_name(cls.__name__ + "-image")
        if 'name' in kwargs:
            name = kwargs.pop('name')

        resp, image = cls.servers_client.create_image(
            server_id, name)
        image_id = data_utils.parse_image_id(resp['location'])
        cls.images.append(image_id)

        if 'wait_until' in kwargs:
            cls.images_client.wait_for_image_status(image_id,
                                                    kwargs['wait_until'])
            resp, image = cls.images_client.get_image_meta(image_id)

        return resp, image

    @classmethod
    def rebuild_server(cls, server_id, **kwargs):
        # Destroy an existing server and creates a new one
        try:
            cls.servers_client.delete_server(server_id)
            cls.servers_client.wait_for_server_termination(server_id)
        except Exception as exc:
            LOG.exception(exc)
            pass
        resp, server = cls.create_test_server(wait_until='ACTIVE', **kwargs)
        cls.password = server['admin_password']
        return server['id']


class BaseV3ComputeAdminTest(BaseV3ComputeTest):
    """Base test case class for all Compute Admin API V3 tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseV3ComputeAdminTest, cls).setUpClass()
        admin_username = cls.config.compute_admin.username
        admin_password = cls.config.compute_admin.password
        admin_tenant = cls.config.compute_admin.tenant_name
        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Compute Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = creds
            os_adm = clients.Manager(username=admin_username,
                                     password=admin_password,
                                     tenant_name=admin_tenant_name,
                                     interface=cls._interface)
        else:
            os_adm = clients.ComputeAdminManager(interface=cls._interface)

        cls.os_adm = os_adm
        cls.severs_admin_client = cls.os_adm.servers_v3_client
        cls.services_admin_client = cls.os_adm.services_v3_client
        cls.availability_zone_admin_client = \
            cls.os_adm.availability_zone_v3_client
        cls.hypervisor_admin_client = cls.os_adm.hypervisor_v3_client
        cls.tenant_usages_admin_client = cls.os_adm.tenant_usages_v3_client
