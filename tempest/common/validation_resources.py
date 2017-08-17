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
    if use_neutron:
        return os.network
    else:
        return os.compute


def create_ssh_security_group(os, add_rule=False, ethertype='IPv4',
                              use_neutron=True):
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
    # Cleanup the vm validation resources
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
