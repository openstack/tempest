# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log as logging

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)


def _network_service(os, use_neutron):
    # Internal helper to select the right network clients
    if use_neutron:
        return os.network
    else:
        return os.compute


def create_ssh_security_group(os, add_rule=False, ethertype='IPv4',
                              use_neutron=True):
    """Create a security group for ping/ssh testing

    Create a security group to be attached to a VM using the nova or neutron
    clients. If rules are added, the group can be attached to a VM to enable
    connectivity validation over ICMP and further testing over SSH.

    :param os: An instance of `tempest.lib.services.clients.ServiceClients` or
        of a subclass of it. Resources are provisioned using clients from `os`.
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
        os = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Security group for IPv4 tests
        sg4 = vr.create_ssh_security_group(os, add_rule=True)
        # Security group for IPv6 tests
        sg6 = vr.create_ssh_security_group(os, ethertype='IPv6', add_rule=True)
    """
    network_service = _network_service(os, use_neutron)
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
    LOG.debug("SSH Validation resource security group with tcp and icmp "
              "rules %s created", sg_name)
    return security_group


def create_validation_resources(os, validation_resources=None,
                                ethertype='IPv4', use_neutron=True,
                                floating_network_id=None,
                                floating_network_name=None):
    """Provision resources for VM ping/ssh testing

    Create resources required to be able to ping / ssh a virtual machine:
    keypair, security group, security group rules and a floating IP.
    Which of those resources are required may depend on the cloud setup and on
    the specific test and it can be controlled via the validation_resources
    dictionary.

    Provisioned resources are returned in a dictionary.

    :param os: An instance of `tempest.lib.services.clients.ServiceClients` or
        of a subclass of it. Resources are provisioned using clients from `os`.
    :param validation_resources: A dictionary that specifies which resources to
        provision. Required keys are: 'keypair', 'security_group',
        'security_group_rules' and 'floating_ip'.
    :param ethertype: 'IPv4' or 'IPv6'. Honoured only in case neutron is used.
    :param use_neutron: When True resources are provisioned via neutron, when
        False resources are provisioned via nova.
    :param floating_network_id: The id of the network used to provision a
        floating IP. Only used if a floating IP is requested and with neutron.
    :param floating_network_name: The name of the floating IP pool used to
        provision the floating IP. Only used if a floating IP is requested and
        with nova-net.
    :returns: A dictionary with the same keys as the input
        `validation_resources` and the resources for values in the format
         they are returned by the API.

    Examples::

        from tempest.common import validation_resources as vr
        from tempest.lib import auth
        from tempest.lib.services import clients

        creds = auth.get_credentials('http://mycloud/identity/v3',
                                     username='me', project_name='me',
                                     password='secret', domain_name='Default')
        os = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Request keypair and floating IP
        resources = dict(keypair=True, security_group=False,
                         security_group_rules=False, floating_ip=True)
        resources = vr.create_validation_resources(
            os, validation_resources=resources, use_neutron=True,
            floating_network_id='4240E68E-23DA-4C82-AC34-9FEFAA24521C')

        # The floating IP to be attached to the VM
        floating_ip = resources['floating_ip']['ip']
    """
    # Create and Return the validation resources required to validate a VM
    validation_data = {}
    if validation_resources:
        if validation_resources['keypair']:
            keypair_name = data_utils.rand_name('keypair')
            validation_data.update(os.compute.KeyPairsClient().create_keypair(
                name=keypair_name))
            LOG.debug("Validation resource key %s created", keypair_name)
        add_rule = False
        if validation_resources['security_group']:
            if validation_resources['security_group_rules']:
                add_rule = True
            validation_data['security_group'] = \
                create_ssh_security_group(
                    os, add_rule, use_neutron=use_neutron, ethertype=ethertype)
        if validation_resources['floating_ip']:
            floating_ip_client = _network_service(
                os, use_neutron).FloatingIPsClient()
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
    return validation_data


def clear_validation_resources(os, validation_data=None, use_neutron=True):
    """Cleanup resources for VM ping/ssh testing

    Cleanup a set of resources provisioned via `create_validation_resources`.
    In case of errors during cleanup, the exception is logged and the cleanup
    process is continued. The first exception that was raised is re-raised
    after the cleanup is complete.

    :param os: An instance of `tempest.lib.services.clients.ServiceClients` or
        of a subclass of it. Resources are provisioned using clients from `os`.
    :param validation_data: A dictionary that specifies resources to be
        cleaned up in the format returned by `create_validation_resources`.
        Required keys are: 'keypair', 'security_group', 'security_group_rules'
        and 'floating_ip'.
    :param use_neutron: When True resources are provisioned via neutron, when
        False resources are provisioned via nova.
    :returns: A dictionary with the same keys as the input
        `validation_resources` and the resources for values in the format
         they are returned by the API.

    Examples::

        from tempest.common import validation_resources as vr
        from tempest.lib import auth
        from tempest.lib.services import clients

        creds = auth.get_credentials('http://mycloud/identity/v3',
                                     username='me', project_name='me',
                                     password='secret', domain_name='Default')
        os = clients.ServiceClients(creds, 'http://mycloud/identity/v3')
        # Request keypair and floating IP
        resources = dict(keypair=True, security_group=False,
                         security_group_rules=False, floating_ip=True)
        resources = vr.create_validation_resources(
            os, validation_resources=resources, use_neutron=True,
            floating_network_id='4240E68E-23DA-4C82-AC34-9FEFAA24521C')

        # Now cleanup the resources
        try:
            vr.clear_validation_resources(os, resources)
        except Exception as e:
            LOG.exception('Something went wrong during cleanup, ignoring')
    """
    has_exception = None
    if validation_data:
        if 'keypair' in validation_data:
            keypair_client = os.compute.KeyPairsClient()
            keypair_name = validation_data['keypair']['name']
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
        network_service = _network_service(os, use_neutron)
        if 'security_group' in validation_data:
            security_group_client = network_service.SecurityGroupsClient()
            sec_id = validation_data['security_group']['id']
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
        if 'floating_ip' in validation_data:
            floating_ip_client = network_service.FloatingIPsClient()
            fip_id = validation_data['floating_ip']['id']
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
