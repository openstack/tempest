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

from tempest import config

from tempest.common.utils import data_utils
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
LOG = logging.getLogger(__name__)


def create_ssh_security_group(os, add_rule=False):
    security_groups_client = os.compute_security_groups_client
    security_group_rules_client = os.compute_security_group_rules_client
    sg_name = data_utils.rand_name('securitygroup-')
    sg_description = data_utils.rand_name('description-')
    security_group = security_groups_client.create_security_group(
        name=sg_name, description=sg_description)['security_group']
    if add_rule:
        security_group_rules_client.create_security_group_rule(
            parent_group_id=security_group['id'], ip_protocol='tcp',
            from_port=22, to_port=22)
        security_group_rules_client.create_security_group_rule(
            parent_group_id=security_group['id'], ip_protocol='icmp',
            from_port=-1, to_port=-1)
    LOG.debug("SSH Validation resource security group with tcp and icmp "
              "rules %s created"
              % sg_name)
    return security_group


def create_validation_resources(os, validation_resources=None):
    # Create and Return the validation resources required to validate a VM
    validation_data = {}
    if validation_resources:
        if validation_resources['keypair']:
            keypair_name = data_utils.rand_name('keypair')
            validation_data.update(os.keypairs_client.create_keypair(
                name=keypair_name))
            LOG.debug("Validation resource key %s created" % keypair_name)
        add_rule = False
        if validation_resources['security_group']:
            if validation_resources['security_group_rules']:
                add_rule = True
            validation_data['security_group'] = \
                create_ssh_security_group(os, add_rule)
        if validation_resources['floating_ip']:
            floating_client = os.compute_floating_ips_client
            validation_data.update(
                floating_client.create_floating_ip(
                    pool=CONF.network.floating_network_name))
    return validation_data


def clear_validation_resources(os, validation_data=None):
    # Cleanup the vm validation resources
    has_exception = None
    if validation_data:
        if 'keypair' in validation_data:
            keypair_client = os.keypairs_client
            keypair_name = validation_data['keypair']['name']
            try:
                keypair_client.delete_keypair(keypair_name)
            except lib_exc.NotFound:
                LOG.warning("Keypair %s is not found when attempting to delete"
                            % keypair_name)
            except Exception as exc:
                LOG.exception('Exception raised while deleting key %s'
                              % keypair_name)
                if not has_exception:
                    has_exception = exc
        if 'security_group' in validation_data:
            security_group_client = os.compute_security_groups_client
            sec_id = validation_data['security_group']['id']
            try:
                security_group_client.delete_security_group(sec_id)
                security_group_client.wait_for_resource_deletion(sec_id)
            except lib_exc.NotFound:
                LOG.warning("Security group %s is not found when attempting "
                            "to delete" % sec_id)
            except lib_exc.Conflict as exc:
                LOG.exception('Conflict while deleting security '
                              'group %s VM might not be deleted ' % sec_id)
                if not has_exception:
                    has_exception = exc
            except Exception as exc:
                LOG.exception('Exception raised while deleting security '
                              'group %s ' % sec_id)
                if not has_exception:
                    has_exception = exc
        if 'floating_ip' in validation_data:
            floating_client = os.compute_floating_ips_client
            fip_id = validation_data['floating_ip']['id']
            try:
                floating_client.delete_floating_ip(fip_id)
            except lib_exc.NotFound:
                LOG.warning('Floating ip %s not found while attempting to '
                            'delete' % fip_id)
            except Exception as exc:
                LOG.exception('Exception raised while deleting ip %s '
                              % fip_id)
                if not has_exception:
                    has_exception = exc
    if has_exception:
        raise has_exception
