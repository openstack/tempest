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

from tempest.common import compute
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib.common import api_microversion_fixture
from tempest.lib.common import api_version_request
from tempest.lib.common import api_version_utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseV2ComputeTest(api_version_utils.BaseMicroversionTest,
                        tempest.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    force_tenant_isolation = False
    # Set this to True in subclasses to create a default network. See
    # https://bugs.launchpad.net/tempest/+bug/1844568
    create_default_network = False

    # TODO(andreaf) We should care also for the alt_manager here
    # but only once client lazy load in the manager is done
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseV2ComputeTest, cls).skip_checks()
        if not CONF.service_available.nova:
            raise cls.skipException("Nova is not available")
        api_version_utils.check_skip_with_microversion(
            cls.min_microversion, cls.max_microversion,
            CONF.compute.min_microversion, CONF.compute.max_microversion)
        api_version_utils.check_skip_with_microversion(
            cls.volume_min_microversion, cls.volume_max_microversion,
            CONF.volume.min_microversion, CONF.volume.max_microversion)
        api_version_utils.check_skip_with_microversion(
            cls.placement_min_microversion, cls.placement_max_microversion,
            CONF.placement.min_microversion, CONF.placement.max_microversion)

    @classmethod
    def setup_credentials(cls):
        # Setting network=True, subnet=True creates a default network
        cls.set_network_resources(
            network=cls.create_default_network,
            subnet=cls.create_default_network)
        super(BaseV2ComputeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseV2ComputeTest, cls).setup_clients()
        cls.servers_client = cls.os_primary.servers_client
        cls.server_groups_client = cls.os_primary.server_groups_client
        cls.flavors_client = cls.os_primary.flavors_client
        cls.compute_images_client = cls.os_primary.compute_images_client
        cls.extensions_client = cls.os_primary.extensions_client
        cls.floating_ip_pools_client = cls.os_primary.floating_ip_pools_client
        cls.floating_ips_client = cls.os_primary.compute_floating_ips_client
        cls.keypairs_client = cls.os_primary.keypairs_client
        cls.security_group_rules_client = (
            cls.os_primary.compute_security_group_rules_client)
        cls.security_groups_client =\
            cls.os_primary.compute_security_groups_client
        cls.quotas_client = cls.os_primary.quotas_client
        cls.compute_networks_client = cls.os_primary.compute_networks_client
        cls.limits_client = cls.os_primary.limits_client
        cls.volumes_extensions_client =\
            cls.os_primary.volumes_extensions_client
        cls.snapshots_extensions_client =\
            cls.os_primary.snapshots_extensions_client
        cls.interfaces_client = cls.os_primary.interfaces_client
        cls.fixed_ips_client = cls.os_primary.fixed_ips_client
        cls.availability_zone_client = cls.os_primary.availability_zone_client
        cls.agents_client = cls.os_primary.agents_client
        cls.aggregates_client = cls.os_primary.aggregates_client
        cls.services_client = cls.os_primary.services_client
        cls.instance_usages_audit_log_client = (
            cls.os_primary.instance_usages_audit_log_client)
        cls.hypervisor_client = cls.os_primary.hypervisor_client
        cls.certificates_client = cls.os_primary.certificates_client
        cls.migrations_client = cls.os_primary.migrations_client
        cls.security_group_default_rules_client = (
            cls.os_primary.security_group_default_rules_client)
        cls.versions_client = cls.os_primary.compute_versions_client
        if CONF.service_available.cinder:
            cls.volumes_client = cls.os_primary.volumes_client_latest
            cls.attachments_client = cls.os_primary.attachments_client_latest
            cls.snapshots_client = cls.os_primary.snapshots_client_latest
        if CONF.service_available.glance:
            if CONF.image_feature_enabled.api_v1:
                cls.images_client = cls.os_primary.image_client
            elif CONF.image_feature_enabled.api_v2:
                cls.images_client = cls.os_primary.image_client_v2
            else:
                raise lib_exc.InvalidConfiguration(
                    'Either api_v1 or api_v2 must be True in '
                    '[image-feature-enabled].')
        cls._check_depends_on_nova_network()

    @classmethod
    def _check_depends_on_nova_network(cls):
        # Since nova-network APIs were removed from Nova in the Rocky release,
        # determine, based on the max version from the version document, if
        # the compute API is >Queens and if so, skip tests that rely on
        # nova-network.
        if not getattr(cls, 'depends_on_nova_network', False):
            return
        versions = cls.versions_client.list_versions()['versions']
        # Find the v2.1 version which will tell us our max version for the
        # compute API we're testing against.
        for version in versions:
            if version['id'] == 'v2.1':
                max_version = api_version_request.APIVersionRequest(
                    version['version'])
                break
        else:
            LOG.warning(
                'Unable to determine max v2.1 compute API version: %s',
                versions)
            return

        # The max compute API version in Queens is 2.60 so we cap
        # at that version.
        queens = api_version_request.APIVersionRequest('2.60')
        if max_version > queens:
            raise cls.skipException('nova-network is gone')

    @classmethod
    def resource_setup(cls):
        super(BaseV2ComputeTest, cls).resource_setup()
        cls.request_microversion = (
            api_version_utils.select_request_microversion(
                cls.min_microversion,
                CONF.compute.min_microversion))
        cls.volume_request_microversion = (
            api_version_utils.select_request_microversion(
                cls.volume_min_microversion,
                CONF.volume.min_microversion))
        cls.placement_request_microversion = (
            api_version_utils.select_request_microversion(
                cls.placement_min_microversion,
                CONF.placement.min_microversion))
        cls.build_interval = CONF.compute.build_interval
        cls.build_timeout = CONF.compute.build_timeout
        cls.image_ref = CONF.compute.image_ref
        cls.image_ref_alt = CONF.compute.image_ref_alt
        cls.flavor_ref = CONF.compute.flavor_ref
        cls.flavor_ref_alt = CONF.compute.flavor_ref_alt
        cls.ssh_user = CONF.validation.image_ssh_user
        cls.image_ssh_user = CONF.validation.image_ssh_user
        cls.image_ssh_password = CONF.validation.image_ssh_password

    @classmethod
    def is_requested_microversion_compatible(cls, max_version):
        """Check the compatibility of selected request microversion

        This method will check if selected request microversion
        (cls.request_microversion) for test is compatible with respect
        to 'max_version'. Compatible means if selected request microversion
        is in the range(<=) of 'max_version'.

        :param max_version: maximum microversion to compare for compatibility.
            Example: '2.30'
        :returns: True if selected request microversion is compatible with
            'max_version'. False in other case.
        """
        try:
            req_version_obj = api_version_request.APIVersionRequest(
                cls.request_microversion)
        # NOTE(gmann): This is case where this method is used before calling
        # resource_setup(), where cls.request_microversion is set. There may
        # not be any such case but still we can handle this case.
        except AttributeError:
            request_microversion = (
                api_version_utils.select_request_microversion(
                    cls.min_microversion,
                    CONF.compute.min_microversion))
            req_version_obj = api_version_request.APIVersionRequest(
                request_microversion)
        max_version_obj = api_version_request.APIVersionRequest(max_version)
        return req_version_obj <= max_version_obj

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
    def create_test_server(cls, validatable=False, volume_backed=False,
                           validation_resources=None, clients=None, **kwargs):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server. The purpose of this wrapper is to minimize
        the impact on the code of the tests already using this
        function.

        :param validatable: Whether the server will be pingable or sshable.
        :param volume_backed: Whether the instance is volume backed or not.
        :param validation_resources: Dictionary of validation resources as
            returned by `get_class_validation_resources`.
        :param clients: Client manager, defaults to os_primary.
        :param kwargs: Extra arguments are passed down to the
            `compute.create_test_server` call.
        """
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(cls.__name__ + "-server")

        request_version = api_version_request.APIVersionRequest(
            cls.request_microversion)
        v2_37_version = api_version_request.APIVersionRequest('2.37')

        tenant_network = cls.get_tenant_network()
        # NOTE(snikitin): since microversion v2.37 'networks' field is required
        if (request_version >= v2_37_version and 'networks' not in kwargs and
            not tenant_network):
            kwargs['networks'] = 'none'

        if clients is None:
            clients = cls.os_primary

        body, servers = compute.create_test_server(
            clients,
            validatable,
            validation_resources=validation_resources,
            tenant_network=tenant_network,
            volume_backed=volume_backed,
            **kwargs)

        # For each server schedule wait and delete, so we first delete all
        # and then wait for all
        for server in servers:
            cls.addClassResourceCleanup(waiters.wait_for_server_termination,
                                        clients.servers_client, server['id'])
        for server in servers:
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                clients.servers_client.delete_server, server['id'])

        return body

    @classmethod
    def create_security_group(cls, name=None, description=None):
        if name is None:
            name = data_utils.rand_name(cls.__name__ + "-securitygroup")
        if description is None:
            description = data_utils.rand_name('description')
        body = cls.security_groups_client.create_security_group(
            name=name, description=description)['security_group']
        cls.addClassResourceCleanup(
            test_utils.call_and_ignore_notfound_exc,
            cls.security_groups_client.delete_security_group,
            body['id'])

        return body

    @classmethod
    def create_test_server_group(cls, name="", policy=None):
        if not name:
            name = data_utils.rand_name(cls.__name__ + "-Server-Group")
        if policy is None:
            policy = ['affinity']
        body = cls.server_groups_client.create_server_group(
            name=name, policies=policy)['server_group']
        cls.addClassResourceCleanup(
            test_utils.call_and_ignore_notfound_exc,
            cls.server_groups_client.delete_server_group,
            body['id'])
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

    @classmethod
    def prepare_instance_network(cls):
        if (CONF.validation.auth_method != 'disabled' and
                CONF.validation.connect_method == 'floating'):
            cls.set_network_resources(network=True, subnet=True, router=True,
                                      dhcp=True)

    @classmethod
    def create_image_from_server(cls, server_id, **kwargs):
        """Wrapper utility that returns an image created from the server.

        If compute microversion >= 2.36, the returned image response will
        be from the image service API rather than the compute image proxy API.
        """
        name = kwargs.pop('name',
                          data_utils.rand_name(cls.__name__ + "-image"))
        wait_until = kwargs.pop('wait_until', None)
        wait_for_server = kwargs.pop('wait_for_server', True)

        image = cls.compute_images_client.create_image(server_id, name=name,
                                                       **kwargs)
        if api_version_utils.compare_version_header_to_response(
            "OpenStack-API-Version", "compute 2.45", image.response, "lt"):
            image_id = image['image_id']
        else:
            image_id = data_utils.parse_image_id(image.response['location'])

        # The compute image proxy APIs were deprecated in 2.35 so
        # use the images client directly if the API microversion being
        # used is >=2.36.
        if not cls.is_requested_microversion_compatible('2.35'):
            client = cls.images_client
        else:
            client = cls.compute_images_client
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    client.delete_image, image_id)

        if wait_until is not None:
            try:
                wait_until = wait_until.upper()
                if not cls.is_requested_microversion_compatible('2.35'):
                    wait_until = wait_until.lower()
                waiters.wait_for_image_status(client, image_id, wait_until)
            except lib_exc.NotFound:
                if wait_until.upper() == 'ACTIVE':
                    # If the image is not found after create_image returned
                    # that means the snapshot failed in nova-compute and nova
                    # deleted the image. There should be a compute fault
                    # recorded with the server in that case, so get the server
                    # and dump some details.
                    server = (
                        cls.servers_client.show_server(server_id)['server'])
                    if 'fault' in server:
                        raise exceptions.SnapshotNotFoundException(
                            server['fault'], image_id=image_id)
                    else:
                        raise exceptions.SnapshotNotFoundException(
                            image_id=image_id)
                else:
                    raise
            image = client.show_image(image_id)
            # Compute image client returns response wrapped in 'image' element
            # which is not the case with Glance image client.
            if 'image' in image:
                image = image['image']

            if wait_until.upper() == 'ACTIVE':
                if wait_for_server:
                    waiters.wait_for_server_status(cls.servers_client,
                                                   server_id, 'ACTIVE')
        return image

    @classmethod
    def recreate_server(cls, server_id, validatable=False, **kwargs):
        """Destroy an existing class level server and creates a new one

        Some test classes use a test server that can be used by multiple
        tests. This is done to optimise runtime and test load.
        If something goes wrong with the test server, it can be rebuilt
        using this helper.

        This helper can also be used for the initial provisioning if no
        server_id is specified.

        :param server_id: UUID of the server to be rebuilt. If None is
            specified, a new server is provisioned.
        :param validatable: whether to the server needs to be
            validatable. When True, validation resources are acquired via
            the `get_class_validation_resources` helper.
        :param kwargs: extra paramaters are passed through to the
            `create_test_server` call.
        :return: the UUID of the created server.
        """
        if server_id:
            cls.delete_server(server_id)

        cls.password = data_utils.rand_password()
        server = cls.create_test_server(
            validatable,
            validation_resources=cls.get_class_validation_resources(
                cls.os_primary),
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
            LOG.exception('Failed to delete server %s', server_id)

    def resize_server(self, server_id, new_flavor_id, **kwargs):
        """resize and confirm_resize an server, waits for it to be ACTIVE."""
        self.servers_client.resize_server(server_id, new_flavor_id, **kwargs)
        waiters.wait_for_server_status(self.servers_client, server_id,
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server_id)
        waiters.wait_for_server_status(
            self.servers_client, server_id, 'ACTIVE')
        server = self.servers_client.show_server(server_id)['server']
        self.assert_flavor_equal(new_flavor_id, server['flavor'])

    @classmethod
    def delete_volume(cls, volume_id):
        """Deletes the given volume and waits for it to be gone."""
        try:
            cls.volumes_client.delete_volume(volume_id)
            # TODO(mriedem): We should move the wait_for_resource_deletion
            # into the delete_volume method as a convenience to the caller.
            cls.volumes_client.wait_for_resource_deletion(volume_id)
        except lib_exc.NotFound:
            LOG.warning("Unable to delete volume '%s' since it was not found. "
                        "Maybe it was already deleted?", volume_id)

    @classmethod
    def get_server_ip(cls, server, validation_resources=None):
        """Get the server fixed or floating IP.

        Based on the configuration we're in, return a correct ip
        address for validating that a guest is up.

        :param server: The server dict as returned by the API
        :param validation_resources: The dict of validation resources
            provisioned for the server.
        """
        if CONF.validation.connect_method == 'floating':
            if validation_resources:
                return validation_resources['floating_ip']['ip']
            else:
                msg = ('When validation.connect_method equals floating, '
                       'validation_resources cannot be None')
                raise lib_exc.InvalidParam(invalid_param=msg)
        elif CONF.validation.connect_method == 'fixed':
            addresses = server['addresses'][CONF.validation.network_for_ssh]
            for address in addresses:
                if address['version'] == CONF.validation.ip_version_for_ssh:
                    return address['addr']
            raise exceptions.ServerUnreachable(server_id=server['id'])
        else:
            raise lib_exc.InvalidConfiguration()

    def setUp(self):
        super(BaseV2ComputeTest, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            compute_microversion=self.request_microversion,
            volume_microversion=self.volume_request_microversion,
            placement_microversion=self.placement_request_microversion))

    @classmethod
    def create_volume(cls, image_ref=None, **kwargs):
        """Create a volume and wait for it to become 'available'.

        :param image_ref: Specify an image id to create a bootable volume.
        :param kwargs: other parameters to create volume.
        :returns: The available volume.
        """
        if 'size' not in kwargs:
            kwargs['size'] = CONF.volume.volume_size
        if 'display_name' not in kwargs:
            vol_name = data_utils.rand_name(cls.__name__ + '-volume')
            kwargs['display_name'] = vol_name
        if image_ref is not None:
            kwargs['imageRef'] = image_ref
        if CONF.compute.compute_volume_common_az:
            kwargs.setdefault('availability_zone',
                              CONF.compute.compute_volume_common_az)
        volume = cls.volumes_client.create_volume(**kwargs)['volume']
        cls.addClassResourceCleanup(
            cls.volumes_client.wait_for_resource_deletion, volume['id'])
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.volumes_client.delete_volume,
                                    volume['id'])
        waiters.wait_for_volume_resource_status(cls.volumes_client,
                                                volume['id'], 'available')
        return volume

    def _detach_volume(self, server, volume):
        """Helper method to detach a volume.

        Ignores 404 responses if the volume or server do not exist, or the
        volume is already detached from the server.
        """
        try:
            volume = self.volumes_client.show_volume(volume['id'])['volume']
            # Check the status. You can only detach an in-use volume, otherwise
            # the compute API will return a 400 response.
            if volume['status'] == 'in-use':
                self.servers_client.detach_volume(server['id'], volume['id'])
        except lib_exc.NotFound:
            # Ignore 404s on detach in case the server is deleted or the volume
            # is already detached.
            pass

    def attach_volume(self, server, volume, device=None, tag=None):
        """Attaches volume to server and waits for 'in-use' volume status.

        The volume will be detached when the test tears down.

        :param server: The server to which the volume will be attached.
        :param volume: The volume to attach.
        :param device: Optional mountpoint for the attached volume. Note that
            this is not guaranteed for all hypervisors and is not recommended.
        :param tag: Optional device role tag to apply to the volume.
        """
        attach_kwargs = dict(volumeId=volume['id'])
        if device:
            attach_kwargs['device'] = device
        if tag:
            attach_kwargs['tag'] = tag

        attachment = self.servers_client.attach_volume(
            server['id'], **attach_kwargs)['volumeAttachment']
        # On teardown detach the volume and for multiattach volumes wait for
        # the attachment to be removed. For non-multiattach volumes wait for
        # the state of the volume to change to available. This is so we don't
        # error out when trying to delete the volume during teardown.
        if volume['multiattach']:
            att = waiters.wait_for_volume_attachment_create(
                self.volumes_client, volume['id'], server['id'])
            self.addCleanup(waiters.wait_for_volume_attachment_remove,
                            self.volumes_client, volume['id'],
                            att['attachment_id'])
        else:
            self.addCleanup(waiters.wait_for_volume_resource_status,
                            self.volumes_client, volume['id'], 'available')
            waiters.wait_for_volume_resource_status(self.volumes_client,
                                                    volume['id'], 'in-use')
        # Ignore 404s on detach in case the server is deleted or the volume
        # is already detached.
        self.addCleanup(self._detach_volume, server, volume)
        return attachment

    def create_volume_snapshot(self, volume_id, name=None, description=None,
                               metadata=None, force=False):
        name = name or data_utils.rand_name(
            self.__class__.__name__ + '-snapshot')
        snapshot = self.snapshots_client.create_snapshot(
            volume_id=volume_id,
            force=force,
            display_name=name,
            description=description,
            metadata=metadata)['snapshot']
        self.addCleanup(self.snapshots_client.wait_for_resource_deletion,
                        snapshot['id'])
        self.addCleanup(self.snapshots_client.delete_snapshot, snapshot['id'])
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                snapshot['id'], 'available')
        snapshot = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        return snapshot

    def assert_flavor_equal(self, flavor_id, server_flavor):
        """Check whether server_flavor equals to flavor.

        :param flavor_id: flavor id
        :param server_flavor: flavor info returned by show_server.
        """
        # Nova API > 2.46 no longer includes flavor.id, and schema check
        # will cover whether 'id' should be in flavor
        if server_flavor.get('id'):
            msg = ('server flavor is not same as flavor!')
            self.assertEqual(flavor_id, server_flavor['id'], msg)
        else:
            flavor = self.flavors_client.show_flavor(flavor_id)['flavor']
            self.assertEqual(flavor['name'], server_flavor['original_name'],
                             "original_name in server flavor is not same as "
                             "flavor name!")
            for key in ['ram', 'vcpus', 'disk']:
                msg = ('attribute %s in server flavor is not same as '
                       'flavor!' % key)
                self.assertEqual(flavor[key], server_flavor[key], msg)


class BaseV2ComputeAdminTest(BaseV2ComputeTest):
    """Base test case class for Compute Admin API tests."""

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseV2ComputeAdminTest, cls).setup_clients()
        cls.availability_zone_admin_client = (
            cls.os_admin.availability_zone_client)
        cls.admin_flavors_client = cls.os_admin.flavors_client
        cls.admin_servers_client = cls.os_admin.servers_client

    def create_flavor(self, ram, vcpus, disk, name=None,
                      is_public='True', **kwargs):
        if name is None:
            name = data_utils.rand_name(self.__class__.__name__ + "-flavor")
        id = kwargs.pop('id', data_utils.rand_int_id(start=1000))
        client = self.admin_flavors_client
        flavor = client.create_flavor(
            ram=ram, vcpus=vcpus, disk=disk, name=name,
            id=id, is_public=is_public, **kwargs)['flavor']
        self.addCleanup(client.wait_for_resource_deletion, flavor['id'])
        self.addCleanup(client.delete_flavor, flavor['id'])
        return flavor

    @classmethod
    def get_host_for_server(cls, server_id):
        server_details = cls.admin_servers_client.show_server(server_id)
        return server_details['server']['OS-EXT-SRV-ATTR:host']

    def get_host_other_than(self, server_id):
        source_host = self.get_host_for_server(server_id)

        svcs = self.os_admin.services_client.list_services(
            binary='nova-compute')['services']
        hosts = []
        for svc in svcs:
            if svc['state'] == 'up' and svc['status'] == 'enabled':
                if CONF.compute.compute_volume_common_az:
                    if svc['zone'] == CONF.compute.compute_volume_common_az:
                        hosts.append(svc['host'])
                else:
                    hosts.append(svc['host'])

        for target_host in hosts:
            if source_host != target_host:
                return target_host
