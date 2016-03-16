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

from oslo_log import log as logging

from tempest.api.compute import api_microversion_fixture
from tempest.common import compute
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib.common import api_version_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseV2ComputeTest(api_version_utils.BaseMicroversionTest,
                        tempest.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    force_tenant_isolation = False

    # TODO(andreaf) We should care also for the alt_manager here
    # but only once client lazy load in the manager is done
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseV2ComputeTest, cls).skip_checks()
        if not CONF.service_available.nova:
            raise cls.skipException("Nova is not available")
        cfg_min_version = CONF.compute.min_microversion
        cfg_max_version = CONF.compute.max_microversion
        api_version_utils.check_skip_with_microversion(cls.min_microversion,
                                                       cls.max_microversion,
                                                       cfg_min_version,
                                                       cfg_max_version)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseV2ComputeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseV2ComputeTest, cls).setup_clients()
        cls.servers_client = cls.os.servers_client
        cls.server_groups_client = cls.os.server_groups_client
        cls.flavors_client = cls.os.flavors_client
        cls.compute_images_client = cls.os.compute_images_client
        cls.extensions_client = cls.os.extensions_client
        cls.floating_ip_pools_client = cls.os.floating_ip_pools_client
        cls.floating_ips_client = cls.os.compute_floating_ips_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_group_rules_client = (
            cls.os.compute_security_group_rules_client)
        cls.security_groups_client = cls.os.compute_security_groups_client
        cls.quotas_client = cls.os.quotas_client
        cls.quota_classes_client = cls.os.quota_classes_client
        cls.compute_networks_client = cls.os.compute_networks_client
        cls.limits_client = cls.os.limits_client
        cls.volumes_extensions_client = cls.os.volumes_extensions_client
        cls.snapshots_extensions_client = cls.os.snapshots_extensions_client
        cls.interfaces_client = cls.os.interfaces_client
        cls.fixed_ips_client = cls.os.fixed_ips_client
        cls.availability_zone_client = cls.os.availability_zone_client
        cls.agents_client = cls.os.agents_client
        cls.aggregates_client = cls.os.aggregates_client
        cls.services_client = cls.os.services_client
        cls.instance_usages_audit_log_client = (
            cls.os.instance_usages_audit_log_client)
        cls.hypervisor_client = cls.os.hypervisor_client
        cls.certificates_client = cls.os.certificates_client
        cls.migrations_client = cls.os.migrations_client
        cls.security_group_default_rules_client = (
            cls.os.security_group_default_rules_client)
        cls.versions_client = cls.os.compute_versions_client

        if CONF.volume_feature_enabled.api_v1:
            cls.volumes_client = cls.os.volumes_client
        else:
            cls.volumes_client = cls.os.volumes_v2_client

    @classmethod
    def resource_setup(cls):
        super(BaseV2ComputeTest, cls).resource_setup()
        cls.request_microversion = (
            api_version_utils.select_request_microversion(
                cls.min_microversion,
                CONF.compute.min_microversion))
        cls.build_interval = CONF.compute.build_interval
        cls.build_timeout = CONF.compute.build_timeout
        cls.image_ref = CONF.compute.image_ref
        cls.image_ref_alt = CONF.compute.image_ref_alt
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.flavor_ref_alt = CONF.compute.flavor_ref_alt
        cls.ssh_user = CONF.validation.image_ssh_user
        cls.image_ssh_user = CONF.validation.image_ssh_user
        cls.image_ssh_password = CONF.validation.image_ssh_password
        cls.servers = []
        cls.images = []
        cls.security_groups = []
        cls.server_groups = []

    @classmethod
    def resource_cleanup(cls):
        cls.clear_images()
        cls.clear_servers()
        cls.clear_security_groups()
        cls.clear_server_groups()
        super(BaseV2ComputeTest, cls).resource_cleanup()

    @classmethod
    def clear_servers(cls):
        LOG.debug('Clearing servers: %s', ','.join(
            server['id'] for server in cls.servers))
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except lib_exc.NotFound:
                # Something else already cleaned up the server, nothing to be
                # worried about
                pass
            except Exception:
                LOG.exception('Deleting server %s failed' % server['id'])

        for server in cls.servers:
            try:
                waiters.wait_for_server_termination(cls.servers_client,
                                                    server['id'])
            except Exception:
                LOG.exception('Waiting for deletion of server %s failed'
                              % server['id'])

    @classmethod
    def server_check_teardown(cls):
        """Checks is the shared server clean enough for subsequent test.

           Method will delete the server when it's dirty.
           The setUp method is responsible for creating a new server.
           Exceptions raised in tearDown class are fails the test case,
           This method supposed to use only by tearDown methods, when
           the shared server_id is stored in the server_id of the class.
        """
        if getattr(cls, 'server_id', None) is not None:
            try:
                waiters.wait_for_server_status(cls.servers_client,
                                               cls.server_id, 'ACTIVE')
            except Exception as exc:
                LOG.exception(exc)
                cls.servers_client.delete_server(cls.server_id)
                waiters.wait_for_server_termination(cls.servers_client,
                                                    cls.server_id)
                cls.server_id = None
                raise

    @classmethod
    def clear_images(cls):
        LOG.debug('Clearing images: %s', ','.join(cls.images))
        for image_id in cls.images:
            try:
                cls.compute_images_client.delete_image(image_id)
            except lib_exc.NotFound:
                # The image may have already been deleted which is OK.
                pass
            except Exception:
                LOG.exception('Exception raised deleting image %s' % image_id)

    @classmethod
    def clear_security_groups(cls):
        LOG.debug('Clearing security groups: %s', ','.join(
            str(sg['id']) for sg in cls.security_groups))
        for sg in cls.security_groups:
            try:
                cls.security_groups_client.delete_security_group(sg['id'])
            except lib_exc.NotFound:
                # The security group may have already been deleted which is OK.
                pass
            except Exception as exc:
                LOG.info('Exception raised deleting security group %s',
                         sg['id'])
                LOG.exception(exc)

    @classmethod
    def clear_server_groups(cls):
        LOG.debug('Clearing server groups: %s', ','.join(cls.server_groups))
        for server_group_id in cls.server_groups:
            try:
                cls.server_groups_client.delete_server_group(server_group_id)
            except lib_exc.NotFound:
                # The server-group may have already been deleted which is OK.
                pass
            except Exception:
                LOG.exception('Exception raised deleting server-group %s',
                              server_group_id)

    @classmethod
    def create_test_server(cls, validatable=False, volume_backed=False,
                           **kwargs):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server. The purpose of this wrapper is to minimize
        the impact on the code of the tests already using this
        function.

        :param validatable: Whether the server will be pingable or sshable.
        :param volume_backed: Whether the instance is volume backed or not.
        """
        tenant_network = cls.get_tenant_network()
        body, servers = compute.create_test_server(
            cls.os,
            validatable,
            validation_resources=cls.validation_resources,
            tenant_network=tenant_network,
            volume_backed=volume_backed,
            **kwargs)

        cls.servers.extend(servers)

        return body

    @classmethod
    def create_security_group(cls, name=None, description=None):
        if name is None:
            name = data_utils.rand_name(cls.__name__ + "-securitygroup")
        if description is None:
            description = data_utils.rand_name('description')
        body = cls.security_groups_client.create_security_group(
            name=name, description=description)['security_group']
        cls.security_groups.append(body)

        return body

    @classmethod
    def create_test_server_group(cls, name="", policy=None):
        if not name:
            name = data_utils.rand_name(cls.__name__ + "-Server-Group")
        if policy is None:
            policy = ['affinity']
        body = cls.server_groups_client.create_server_group(
            name=name, policies=policy)['server_group']
        cls.server_groups.append(body['id'])
        return body

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

    @staticmethod
    def _delete_volume(volumes_client, volume_id):
        """Deletes the given volume and waits for it to be gone."""
        try:
            volumes_client.delete_volume(volume_id)
            # TODO(mriedem): We should move the wait_for_resource_deletion
            # into the delete_volume method as a convenience to the caller.
            volumes_client.wait_for_resource_deletion(volume_id)
        except lib_exc.NotFound:
            LOG.warning("Unable to delete volume '%s' since it was not found. "
                        "Maybe it was already deleted?" % volume_id)

    @classmethod
    def prepare_instance_network(cls):
        if (CONF.validation.auth_method != 'disabled' and
                CONF.validation.connect_method == 'floating'):
            cls.set_network_resources(network=True, subnet=True, router=True,
                                      dhcp=True)

    @classmethod
    def create_image_from_server(cls, server_id, **kwargs):
        """Wrapper utility that returns an image created from the server."""
        name = data_utils.rand_name(cls.__name__ + "-image")
        if 'name' in kwargs:
            name = kwargs.pop('name')

        image = cls.compute_images_client.create_image(server_id, name=name)
        image_id = data_utils.parse_image_id(image.response['location'])
        cls.images.append(image_id)

        if 'wait_until' in kwargs:
            waiters.wait_for_image_status(cls.compute_images_client,
                                          image_id, kwargs['wait_until'])
            image = cls.compute_images_client.show_image(image_id)['image']

            if kwargs['wait_until'] == 'ACTIVE':
                if kwargs.get('wait_for_server', True):
                    waiters.wait_for_server_status(cls.servers_client,
                                                   server_id, 'ACTIVE')
        return image

    @classmethod
    def rebuild_server(cls, server_id, validatable=False, **kwargs):
        # Destroy an existing server and creates a new one
        if server_id:
            try:
                cls.servers_client.delete_server(server_id)
                waiters.wait_for_server_termination(cls.servers_client,
                                                    server_id)
            except Exception:
                LOG.exception('Failed to delete server %s' % server_id)

        cls.password = data_utils.rand_password()
        server = cls.create_test_server(
            validatable,
            wait_until='ACTIVE',
            adminPass=cls.password,
            **kwargs)
        return server['id']

    @classmethod
    def delete_server(cls, server_id):
        """Deletes an existing server and waits for it to be gone."""
        try:
            cls.servers_client.delete_server(server_id)
            waiters.wait_for_server_termination(cls.servers_client,
                                                server_id)
        except Exception:
            LOG.exception('Failed to delete server %s' % server_id)

    @classmethod
    def delete_volume(cls, volume_id):
        """Deletes the given volume and waits for it to be gone."""
        cls._delete_volume(cls.volumes_extensions_client, volume_id)

    @classmethod
    def get_server_ip(cls, server):
        """Get the server fixed or floating IP.

        Based on the configuration we're in, return a correct ip
        address for validating that a guest is up.
        """
        if CONF.validation.connect_method == 'floating':
            return cls.validation_resources['floating_ip']['ip']
        elif CONF.validation.connect_method == 'fixed':
            addresses = server['addresses'][CONF.validation.network_for_ssh]
            for address in addresses:
                if address['version'] == CONF.validation.ip_version_for_ssh:
                    return address['addr']
            raise exceptions.ServerUnreachable()
        else:
            raise exceptions.InvalidConfiguration()

    def setUp(self):
        super(BaseV2ComputeTest, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            self.request_microversion))


class BaseV2ComputeAdminTest(BaseV2ComputeTest):
    """Base test case class for Compute Admin API tests."""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseV2ComputeAdminTest, cls).setup_clients()
        cls.availability_zone_admin_client = (
            cls.os_adm.availability_zone_client)
