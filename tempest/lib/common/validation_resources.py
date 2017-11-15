# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2017 IBM Corp.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import fixtures
from oslo_log import log as logging
from oslo_utils import excutils

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)


def _network_service(clients, use_neutron):
    # Internal helper to select the right network clients
    if use_neutron:
        return clients.network
    else:
        return clients.compute


def create_ssh_security_group(clients, add_rule=False, ethertype='IPv4',
                              use_neutron=True):
    """Create a security group for ping/ssh testing

    Create a security group to be attached to a VM using the nova or neutron
    clients. If rules are added, the group can be attached to a VM to enable
    connectivity validation over ICMP and further testing over SSH.

    :param clients: Instance of `tempest.lib.services.clients.ServiceClients`
        or of a subclass of it. Resources are provisioned using clients from
        `clients`.
    :param add_rule: Whether security group rules are provisioned or not.
        Defaults to `False`.
    :param ethertype: 'IPv4' or 'IPv6'. Honoured only in case neutron is used.
    :param use_neutron: When True resources are provisioned via neutron, when
        False resources are provisioned via nova.
    :returns: A dictionary with the security group as returned by the API.

    Examples::

        from tempest.common import validation_resources as vr
        from tempest.lib import auth
        from tempest.lib.services import clients

        creds = auth.get_credentials('http://mycloud/identity/v3',
                                     username='me', project_name='me',
                                     password='secret', domain_name='Default')
        osclients = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Security group for IPv4 tests
        sg4 = vr.create_ssh_security_group(osclients, add_rule=True)
        # Security group for IPv6 tests
        sg6 = vr.create_ssh_security_group(osclients, ethertype='IPv6',
                                           add_rule=True)
    """
    network_service = _network_service(clients, use_neutron)
    security_groups_client = network_service.SecurityGroupsClient()
    security_group_rules_client = network_service.SecurityGroupRulesClient()
    # Security Group clients for nova and neutron behave the same
    sg_name = data_utils.rand_name('securitygroup-')
    sg_description = data_utils.rand_name('description-')
    security_group = security_groups_client.create_security_group(
        name=sg_name, description=sg_description)['security_group']
    # Security Group Rules clients require different parameters depending on
    # the network service in use
    if add_rule:
        try:
            if use_neutron:
                security_group_rules_client.create_security_group_rule(
                    security_group_id=security_group['id'],
                    protocol='tcp',
                    ethertype=ethertype,
                    port_range_min=22,
                    port_range_max=22,
                    direction='ingress')
                security_group_rules_client.create_security_group_rule(
                    security_group_id=security_group['id'],
                    protocol='icmp',
                    ethertype=ethertype,
                    direction='ingress')
            else:
                security_group_rules_client.create_security_group_rule(
                    parent_group_id=security_group['id'], ip_protocol='tcp',
                    from_port=22, to_port=22)
                security_group_rules_client.create_security_group_rule(
                    parent_group_id=security_group['id'], ip_protocol='icmp',
                    from_port=-1, to_port=-1)
        except Exception as sgc_exc:
            # If adding security group rules fails, we cleanup the SG before
            # re-raising the failure up
            with excutils.save_and_reraise_exception():
                try:
                    msg = ('Error while provisioning security group rules in '
                           'security group %s. Trying to cleanup.')
                    # The exceptions logging is already handled, so using
                    # debug here just to provide more context
                    LOG.debug(msg, sgc_exc)
                    clear_validation_resources(
                        clients, keypair=None, floating_ip=None,
                        security_group=security_group,
                        use_neutron=use_neutron)
                except Exception as cleanup_exc:
                    msg = ('Error during cleanup of a security group. '
                           'The cleanup was triggered by an exception during '
                           'the provisioning of security group rules.\n'
                           'Provisioning exception: %s\n'
                           'First cleanup exception: %s')
                    LOG.exception(msg, sgc_exc, cleanup_exc)
    LOG.debug("SSH Validation resource security group with tcp and icmp "
              "rules %s created", sg_name)
    return security_group


def create_validation_resources(clients, keypair=False, floating_ip=False,
                                security_group=False,
                                security_group_rules=False,
                                ethertype='IPv4', use_neutron=True,
                                floating_network_id=None,
                                floating_network_name=None):
    """Provision resources for VM ping/ssh testing

    Create resources required to be able to ping / ssh a virtual machine:
    keypair, security group, security group rules and a floating IP.
    Which of those resources are required may depend on the cloud setup and on
    the specific test and it can be controlled via the corresponding
    arguments.

    Provisioned resources are returned in a dictionary.

    :param clients: Instance of `tempest.lib.services.clients.ServiceClients`
        or of a subclass of it. Resources are provisioned using clients from
        `clients`.
    :param keypair: Whether to provision a keypair. Defaults to False.
    :param floating_ip: Whether to provision a floating IP. Defaults to False.
    :param security_group: Whether to provision a security group. Defaults to
        False.
    :param security_group_rules: Whether to provision security group rules.
        Defaults to False.
    :param ethertype: 'IPv4' or 'IPv6'. Honoured only in case neutron is used.
    :param use_neutron: When True resources are provisioned via neutron, when
        False resources are provisioned via nova.
    :param floating_network_id: The id of the network used to provision a
        floating IP. Only used if a floating IP is requested and with neutron.
    :param floating_network_name: The name of the floating IP pool used to
        provision the floating IP. Only used if a floating IP is requested and
        with nova-net.
    :returns: A dictionary with the resources in the format they are returned
        by the API. Valid keys are 'keypair', 'floating_ip' and
        'security_group'.

    Examples::

        from tempest.common import validation_resources as vr
        from tempest.lib import auth
        from tempest.lib.services import clients

        creds = auth.get_credentials('http://mycloud/identity/v3',
                                     username='me', project_name='me',
                                     password='secret', domain_name='Default')
        osclients = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Request keypair and floating IP
        resources = dict(keypair=True, security_group=False,
                         security_group_rules=False, floating_ip=True)
        resources = vr.create_validation_resources(
            osclients, use_neutron=True,
            floating_network_id='4240E68E-23DA-4C82-AC34-9FEFAA24521C',
            **resources)

        # The floating IP to be attached to the VM
        floating_ip = resources['floating_ip']['ip']
    """
    # Create and Return the validation resources required to validate a VM
    msg = ('Requested validation resources keypair %s, floating IP %s, '
           'security group %s')
    LOG.debug(msg, keypair, floating_ip, security_group)
    validation_data = {}
    try:
        if keypair:
            keypair_name = data_utils.rand_name('keypair')
            validation_data.update(
                clients.compute.KeyPairsClient().create_keypair(
                    name=keypair_name))
            LOG.debug("Validation resource key %s created", keypair_name)
        if security_group:
            validation_data['security_group'] = create_ssh_security_group(
                clients, add_rule=security_group_rules,
                use_neutron=use_neutron, ethertype=ethertype)
        if floating_ip:
            floating_ip_client = _network_service(
                clients, use_neutron).FloatingIPsClient()
            if use_neutron:
                floatingip = floating_ip_client.create_floatingip(
                    floating_network_id=floating_network_id)
                # validation_resources['floating_ip'] has historically looked
                # like a compute API POST /os-floating-ips response, so we need
                # to mangle it a bit for a Neutron response with different
                # fields.
                validation_data['floating_ip'] = floatingip['floatingip']
                validation_data['floating_ip']['ip'] = (
                    floatingip['floatingip']['floating_ip_address'])
            else:
                # NOTE(mriedem): The os-floating-ips compute API was deprecated
                # in the 2.36 microversion. Any tests for CRUD operations on
                # floating IPs using the compute API should be capped at 2.35.
                validation_data.update(floating_ip_client.create_floating_ip(
                    pool=floating_network_name))
            LOG.debug("Validation resource floating IP %s created",
                      validation_data['floating_ip'])
    except Exception as prov_exc:
        # If something goes wrong, cleanup as much as possible before we
        # re-raise the exception
        with excutils.save_and_reraise_exception():
            if validation_data:
                # Cleanup may fail as well
                try:
                    msg = ('Error while provisioning validation resources %s. '
                           'Trying to cleanup what we provisioned so far: %s')
                    # The exceptions logging is already handled, so using
                    # debug here just to provide more context
                    LOG.debug(msg, prov_exc, str(validation_data))
                    clear_validation_resources(
                        clients,
                        keypair=validation_data.get('keypair', None),
                        floating_ip=validation_data.get('floating_ip', None),
                        security_group=validation_data.get('security_group',
                                                           None),
                        use_neutron=use_neutron)
                except Exception as cleanup_exc:
                    msg = ('Error during cleanup of validation resources. '
                           'The cleanup was triggered by an exception during '
                           'the provisioning step.\n'
                           'Provisioning exception: %s\n'
                           'First cleanup exception: %s')
                    LOG.exception(msg, prov_exc, cleanup_exc)
    return validation_data


def clear_validation_resources(clients, keypair=None, floating_ip=None,
                               security_group=None, use_neutron=True):
    """Cleanup resources for VM ping/ssh testing

    Cleanup a set of resources provisioned via `create_validation_resources`.
    In case of errors during cleanup, the exception is logged and the cleanup
    process is continued. The first exception that was raised is re-raised
    after the cleanup is complete.

    :param clients: Instance of `tempest.lib.services.clients.ServiceClients`
        or of a subclass of it. Resources are provisioned using clients from
        `clients`.
    :param keypair: A dictionary with the keypair to be deleted. Defaults to
        None.
    :param floating_ip: A dictionary with the floating_ip to be deleted.
        Defaults to None.
    :param security_group: A dictionary with the security_group to be deleted.
        Defaults to None.
    :param use_neutron: When True resources are provisioned via neutron, when
        False resources are provisioned via nova.

    Examples::

        from tempest.common import validation_resources as vr
        from tempest.lib import auth
        from tempest.lib.services import clients

        creds = auth.get_credentials('http://mycloud/identity/v3',
                                     username='me', project_name='me',
                                     password='secret', domain_name='Default')
        osclients = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Request keypair and floating IP
        resources = dict(keypair=True, security_group=False,
                         security_group_rules=False, floating_ip=True)
        resources = vr.create_validation_resources(
            osclients, validation_resources=resources, use_neutron=True,
            floating_network_id='4240E68E-23DA-4C82-AC34-9FEFAA24521C')

        # Now cleanup the resources
        try:
            vr.clear_validation_resources(osclients, use_neutron=True,
                                          **resources)
        except Exception as e:
            LOG.exception('Something went wrong during cleanup, ignoring')
    """
    has_exception = None
    if keypair:
        keypair_client = clients.compute.KeyPairsClient()
        keypair_name = keypair['name']
        try:
            keypair_client.delete_keypair(keypair_name)
        except lib_exc.NotFound:
            LOG.warning(
                "Keypair %s is not found when attempting to delete",
                keypair_name
            )
        except Exception as exc:
            LOG.exception('Exception raised while deleting key %s',
                          keypair_name)
            if not has_exception:
                has_exception = exc
    network_service = _network_service(clients, use_neutron)
    if security_group:
        security_group_client = network_service.SecurityGroupsClient()
        sec_id = security_group['id']
        try:
            security_group_client.delete_security_group(sec_id)
            security_group_client.wait_for_resource_deletion(sec_id)
        except lib_exc.NotFound:
            LOG.warning("Security group %s is not found when attempting "
                        "to delete", sec_id)
        except lib_exc.Conflict as exc:
            LOG.exception('Conflict while deleting security '
                          'group %s VM might not be deleted', sec_id)
            if not has_exception:
                has_exception = exc
        except Exception as exc:
            LOG.exception('Exception raised while deleting security '
                          'group %s', sec_id)
            if not has_exception:
                has_exception = exc
    if floating_ip:
        floating_ip_client = network_service.FloatingIPsClient()
        fip_id = floating_ip['id']
        try:
            if use_neutron:
                floating_ip_client.delete_floatingip(fip_id)
            else:
                floating_ip_client.delete_floating_ip(fip_id)
        except lib_exc.NotFound:
            LOG.warning('Floating ip %s not found while attempting to '
                        'delete', fip_id)
        except Exception as exc:
            LOG.exception('Exception raised while deleting ip %s', fip_id)
            if not has_exception:
                has_exception = exc
    if has_exception:
        raise has_exception


class ValidationResourcesFixture(fixtures.Fixture):
    """Fixture to provision and cleanup validation resources"""

    DICT_KEYS = ['keypair', 'security_group', 'floating_ip']

    def __init__(self, clients, keypair=False, floating_ip=False,
                 security_group=False, security_group_rules=False,
                 ethertype='IPv4', use_neutron=True, floating_network_id=None,
                 floating_network_name=None):
        """Create a ValidationResourcesFixture

        Create a ValidationResourcesFixture fixtures, which provisions the
        resources required to be able to ping / ssh a virtual machine upon
        setUp and clears them out upon cleanup. Resources are  keypair,
        security group, security group rules and a floating IP - depending
        on the params.

        The fixture exposes a dictionary that includes provisioned resources.

        :param clients: `tempest.lib.services.clients.ServiceClients` or of a
            subclass of it. Resources are provisioned using clients from
            `clients`.
        :param keypair: Whether to provision a keypair. Defaults to False.
        :param floating_ip: Whether to provision a floating IP.
            Defaults to False.
        :param security_group: Whether to provision a security group.
            Defaults to False.
        :param security_group_rules: Whether to provision security group rules.
            Defaults to False.
        :param ethertype: 'IPv4' or 'IPv6'. Honoured only if neutron is used.
        :param use_neutron: When True resources are provisioned via neutron,
            when False resources are provisioned via nova.
        :param floating_network_id: The id of the network used to provision a
            floating IP. Only used if a floating IP is requested in case
            neutron is used.
        :param floating_network_name: The name of the floating IP pool used to
            provision the floating IP. Only used if a floating IP is requested
            and with nova-net.
        :returns: A dictionary with the same keys as the input
            `validation_resources` and the resources for values in the format
             they are returned by the API.

        Examples::

            from tempest.common import validation_resources as vr
            from tempest.lib import auth
            from tempest.lib.services import clients
            import testtools


            class TestWithVR(testtools.TestCase):

                def setUp(self):
                    creds = auth.get_credentials(
                        'http://mycloud/identity/v3',
                         username='me', project_name='me',
                         password='secret', domain_name='Default')

                    osclients = clients.ServiceClients(
                        creds, 'http://mycloud/identity/v3')
                    # Request keypair and floating IP
                    resources = dict(keypair=True, security_group=False,
                                     security_group_rules=False,
                                     floating_ip=True)
                    network_id = '4240E68E-23DA-4C82-AC34-9FEFAA24521C'
                    self.vr = self.useFixture(vr.ValidationResourcesFixture(
                        osclients, use_neutron=True,
                        floating_network_id=network_id,
                        **resources)

                def test_use_ip(self):
                    # The floating IP to be attached to the VM
                    floating_ip = self.vr['floating_ip']['ip']
        """
        self._clients = clients
        self._keypair = keypair
        self._floating_ip = floating_ip
        self._security_group = security_group
        self._security_group_rules = security_group_rules
        self._ethertype = ethertype
        self._use_neutron = use_neutron
        self._floating_network_id = floating_network_id
        self._floating_network_name = floating_network_name
        self._validation_resources = None

    def _setUp(self):
        msg = ('Requested setup of ValidationResources keypair %s, floating '
               'IP %s, security group %s')
        LOG.debug(msg, self._keypair, self._floating_ip, self._security_group)
        self._validation_resources = create_validation_resources(
            self._clients, keypair=self._keypair,
            floating_ip=self._floating_ip,
            security_group=self._security_group,
            security_group_rules=self._security_group_rules,
            ethertype=self._ethertype, use_neutron=self._use_neutron,
            floating_network_id=self._floating_network_id,
            floating_network_name=self._floating_network_name)
        # If provisioning raises an exception we won't have anything to
        # cleanup here, so we don't need a try-finally around provisioning
        vr = self._validation_resources
        self.addCleanup(clear_validation_resources, self._clients,
                        keypair=vr.get('keypair', None),
                        floating_ip=vr.get('floating_ip', None),
                        security_group=vr.get('security_group', None),
                        use_neutron=self._use_neutron)

    @property
    def resources(self):
        return self._validation_resources
