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
from oslo_utils import excutils
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest import clients
from tempest.common import credentials
from tempest.common import fixed_network
from tempest import config
from tempest import exceptions
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseComputeTest(tempest.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    _api_version = 2
    force_tenant_isolation = False

    @classmethod
    def skip_checks(cls):
        super(BaseComputeTest, cls).skip_checks()
        if cls._api_version != 2:
            msg = ("Unexpected API version is specified (%s)" %
                   cls._api_version)
            raise exceptions.InvalidConfiguration(message=msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseComputeTest, cls).setup_credentials()
        # TODO(andreaf) WE should care also for the alt_manager here
        # but only once client lazy load in the manager is done
        cls.os = cls.get_client_manager()
        # Note that we put this here and not in skip_checks because in
        # the case of preprovisioned users we won't know if we can get
        # two distinct users until we go and lock them
        cls.multi_user = cls.check_multi_user()

    @classmethod
    def setup_clients(cls):
        super(BaseComputeTest, cls).setup_clients()
        cls.servers_client = cls.os.servers_client
        cls.flavors_client = cls.os.flavors_client
        cls.images_client = cls.os.images_client
        cls.extensions_client = cls.os.extensions_client
        cls.floating_ips_client = cls.os.floating_ips_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_groups_client = cls.os.security_groups_client
        cls.quotas_client = cls.os.quotas_client
        # NOTE(mriedem): os-quota-class-sets is v2 API only
        cls.quota_classes_client = cls.os.quota_classes_client
        # NOTE(mriedem): os-networks is v2 API only
        cls.networks_client = cls.os.networks_client
        cls.limits_client = cls.os.limits_client
        cls.volumes_extensions_client = cls.os.volumes_extensions_client
        cls.volumes_client = cls.os.volumes_client
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

    @classmethod
    def resource_setup(cls):
        super(BaseComputeTest, cls).resource_setup()
        cls.build_interval = CONF.compute.build_interval
        cls.build_timeout = CONF.compute.build_timeout
        cls.ssh_user = CONF.compute.ssh_user
        cls.image_ref = CONF.compute.image_ref
        cls.image_ref_alt = CONF.compute.image_ref_alt
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.flavor_ref_alt = CONF.compute.flavor_ref_alt
        cls.image_ssh_user = CONF.compute.image_ssh_user
        cls.image_ssh_password = CONF.compute.image_ssh_password
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
        super(BaseComputeTest, cls).resource_cleanup()

    @classmethod
    def check_multi_user(cls):
        # We have a list of accounts now, so just checking if the list is gt 2
        if not cls.isolated_creds.is_multi_user():
            msg = "Not enough users available for multi-user testing"
            raise exceptions.InvalidConfiguration(msg)
        return True

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
                cls.servers_client.wait_for_server_termination(server['id'])
            except Exception:
                LOG.exception('Waiting for deletion of server %s failed'
                              % server['id'])

    @classmethod
    def server_check_teardown(cls):
        """Checks is the shared server clean enough for subsequent test.
           Method will delete the server when it's dirty.
           The setUp method is responsible for creating a new server.
           Exceptions raised in tearDown class are fails the test case,
           This method supposed to use only by tierDown methods, when
           the shared server_id is stored in the server_id of the class.
        """
        if getattr(cls, 'server_id', None) is not None:
            try:
                cls.servers_client.wait_for_server_status(cls.server_id,
                                                          'ACTIVE')
            except Exception as exc:
                LOG.exception(exc)
                cls.servers_client.delete_server(cls.server_id)
                cls.servers_client.wait_for_server_termination(cls.server_id)
                cls.server_id = None
                raise

    @classmethod
    def clear_images(cls):
        LOG.debug('Clearing images: %s', ','.join(cls.images))
        for image_id in cls.images:
            try:
                cls.images_client.delete_image(image_id)
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
                cls.servers_client.delete_server_group(server_group_id)
            except lib_exc.NotFound:
                # The server-group may have already been deleted which is OK.
                pass
            except Exception:
                LOG.exception('Exception raised deleting server-group %s',
                              server_group_id)

    @classmethod
    def create_test_server(cls, **kwargs):
        """Wrapper utility that returns a test server."""
        name = data_utils.rand_name(cls.__name__ + "-instance")
        if 'name' in kwargs:
            name = kwargs.pop('name')
        flavor = kwargs.get('flavor', cls.flavor_ref)
        image_id = kwargs.get('image_id', cls.image_ref)

        kwargs = fixed_network.set_networks_kwarg(
            cls.get_tenant_network(), kwargs) or {}
        body = cls.servers_client.create_server(
            name, image_id, flavor, **kwargs)

        # handle the case of multiple servers
        servers = [body]
        if 'min_count' in kwargs or 'max_count' in kwargs:
            # Get servers created which name match with name param.
            b = cls.servers_client.list_servers()
            servers = [s for s in b['servers'] if s['name'].startswith(name)]

        if 'wait_until' in kwargs:
            for server in servers:
                try:
                    cls.servers_client.wait_for_server_status(
                        server['id'], kwargs['wait_until'])
                except Exception:
                    with excutils.save_and_reraise_exception():
                        if ('preserve_server_on_error' not in kwargs
                            or kwargs['preserve_server_on_error'] is False):
                            for server in servers:
                                try:
                                    cls.servers_client.delete_server(
                                        server['id'])
                                except Exception:
                                    pass

        cls.servers.extend(servers)

        return body

    @classmethod
    def create_security_group(cls, name=None, description=None):
        if name is None:
            name = data_utils.rand_name(cls.__name__ + "-securitygroup")
        if description is None:
            description = data_utils.rand_name('description')
        body = \
            cls.security_groups_client.create_security_group(name,
                                                             description)
        cls.security_groups.append(body)

        return body

    @classmethod
    def create_test_server_group(cls, name="", policy=None):
        if not name:
            name = data_utils.rand_name(cls.__name__ + "-Server-Group")
        if policy is None:
            policy = ['affinity']
        body = cls.servers_client.create_server_group(name, policy)
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
            LOG.warn("Unable to delete volume '%s' since it was not found. "
                     "Maybe it was already deleted?" % volume_id)

    @classmethod
    def prepare_instance_network(cls):
        if (CONF.compute.ssh_auth_method != 'disabled' and
                CONF.compute.ssh_connect_method == 'floating'):
            cls.set_network_resources(network=True, subnet=True, router=True,
                                      dhcp=True)

    @classmethod
    def create_image_from_server(cls, server_id, **kwargs):
        """Wrapper utility that returns an image created from the server."""
        name = data_utils.rand_name(cls.__name__ + "-image")
        if 'name' in kwargs:
            name = kwargs.pop('name')

        image = cls.images_client.create_image(server_id, name)
        image_id = data_utils.parse_image_id(image.response['location'])
        cls.images.append(image_id)

        if 'wait_until' in kwargs:
            cls.images_client.wait_for_image_status(image_id,
                                                    kwargs['wait_until'])
            image = cls.images_client.get_image(image_id)

            if kwargs['wait_until'] == 'ACTIVE':
                if kwargs.get('wait_for_server', True):
                    cls.servers_client.wait_for_server_status(server_id,
                                                              'ACTIVE')
        return image

    @classmethod
    def rebuild_server(cls, server_id, **kwargs):
        # Destroy an existing server and creates a new one
        if server_id:
            try:
                cls.servers_client.delete_server(server_id)
                cls.servers_client.wait_for_server_termination(server_id)
            except Exception:
                LOG.exception('Failed to delete server %s' % server_id)
        server = cls.create_test_server(wait_until='ACTIVE', **kwargs)
        cls.password = server['adminPass']
        return server['id']

    @classmethod
    def delete_volume(cls, volume_id):
        """Deletes the given volume and waits for it to be gone."""
        cls._delete_volume(cls.volumes_extensions_client, volume_id)


class BaseV2ComputeTest(BaseComputeTest):
    _api_version = 2


class BaseComputeAdminTest(BaseComputeTest):
    """Base test case class for Compute Admin API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseComputeAdminTest, cls).skip_checks()
        if not credentials.is_admin_available():
            msg = ("Missing Identity Admin API credentials in configuration.")
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        super(BaseComputeAdminTest, cls).setup_credentials()
        creds = cls.isolated_creds.get_admin_creds()
        cls.os_adm = clients.Manager(credentials=creds)

    @classmethod
    def setup_clients(cls):
        super(BaseComputeAdminTest, cls).setup_clients()
        cls.availability_zone_admin_client = (
            cls.os_adm.availability_zone_client)


class BaseV2ComputeAdminTest(BaseComputeAdminTest):
    """Base test case class for Compute Admin V2 API tests."""
    _api_version = 2
