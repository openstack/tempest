#!/usr/bin/env python

# Copyright 2015 Dell Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

from tempest import clients
from tempest.common import credentials_factory as credentials
from tempest.common import identity
from tempest.common import utils
from tempest.common.utils import net_info
from tempest import config

LOG = logging.getLogger(__name__)
CONF = config.CONF

CONF_FLAVORS = None
CONF_IMAGES = None
CONF_NETWORKS = []
CONF_PRIV_NETWORK_NAME = None
CONF_PUB_NETWORK = None
CONF_PUB_ROUTER = None
CONF_PROJECTS = None
CONF_USERS = None

IS_CINDER = None
IS_GLANCE = None
IS_NEUTRON = None
IS_NOVA = None


def init_conf():
    global CONF_FLAVORS
    global CONF_IMAGES
    global CONF_NETWORKS
    global CONF_PRIV_NETWORK
    global CONF_PRIV_NETWORK_NAME
    global CONF_PUB_NETWORK
    global CONF_PUB_ROUTER
    global CONF_PROJECTS
    global CONF_USERS
    global IS_CINDER
    global IS_GLANCE
    global IS_HEAT
    global IS_NEUTRON
    global IS_NOVA

    IS_CINDER = CONF.service_available.cinder
    IS_GLANCE = CONF.service_available.glance
    IS_NEUTRON = CONF.service_available.neutron
    IS_NOVA = CONF.service_available.nova

    CONF_FLAVORS = [CONF.compute.flavor_ref, CONF.compute.flavor_ref_alt]
    CONF_IMAGES = [CONF.compute.image_ref, CONF.compute.image_ref_alt]
    CONF_PRIV_NETWORK_NAME = CONF.compute.fixed_network_name
    CONF_PUB_NETWORK = CONF.network.public_network_id
    CONF_PUB_ROUTER = CONF.network.public_router_id
    CONF_PROJECTS = [CONF.auth.admin_project_name]
    CONF_USERS = [CONF.auth.admin_username]

    if IS_NEUTRON:
        CONF_PRIV_NETWORK = _get_network_id(CONF.compute.fixed_network_name,
                                            CONF.auth.admin_project_name)
        CONF_NETWORKS = [CONF_PUB_NETWORK, CONF_PRIV_NETWORK]


def _get_network_id(net_name, project_name):
    am = clients.Manager(
        credentials.get_configured_admin_credentials())
    net_cl = am.networks_client
    pr_cl = am.projects_client

    networks = net_cl.list_networks()
    project = identity.get_project_by_name(pr_cl, project_name)
    p_id = project['id']
    n_id = None
    for net in networks['networks']:
        if (net['project_id'] == p_id and net['name'] == net_name):
            n_id = net['id']
            break
    return n_id


class BaseService(object):
    def __init__(self, kwargs):
        self.client = None
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.tenant_filter = {}
        if hasattr(self, 'tenant_id'):
            self.tenant_filter['tenant_id'] = self.tenant_id

    def _filter_by_tenant_id(self, item_list):
        if (item_list is None
                or not item_list
                or not hasattr(self, 'tenant_id')
                or self.tenant_id is None
                or 'tenant_id' not in item_list[0]):
            return item_list

        return [item for item in item_list
                if item['tenant_id'] == self.tenant_id]

    def list(self):
        pass

    def delete(self):
        pass

    def dry_run(self):
        pass

    def save_state(self):
        pass

    def run(self):
        if self.is_dry_run:
            self.dry_run()
        elif self.is_save_state:
            self.save_state()
        else:
            self.delete()


class SnapshotService(BaseService):

    def __init__(self, manager, **kwargs):
        super(SnapshotService, self).__init__(kwargs)
        self.client = manager.snapshots_client_latest

    def list(self):
        client = self.client
        snaps = client.list_snapshots()['snapshots']
        LOG.debug("List count, %s Snapshots", len(snaps))
        return snaps

    def delete(self):
        snaps = self.list()
        client = self.client
        for snap in snaps:
            try:
                client.delete_snapshot(snap['id'])
            except Exception:
                LOG.exception("Delete Snapshot exception.")

    def dry_run(self):
        snaps = self.list()
        self.data['snapshots'] = snaps


class ServerService(BaseService):
    def __init__(self, manager, **kwargs):
        super(ServerService, self).__init__(kwargs)
        self.client = manager.servers_client
        self.server_groups_client = manager.server_groups_client

    def list(self):
        client = self.client
        servers_body = client.list_servers()
        servers = servers_body['servers']
        LOG.debug("List count, %s Servers", len(servers))
        return servers

    def delete(self):
        client = self.client
        servers = self.list()
        for server in servers:
            try:
                client.delete_server(server['id'])
            except Exception:
                LOG.exception("Delete Server exception.")

    def dry_run(self):
        servers = self.list()
        self.data['servers'] = servers


class ServerGroupService(ServerService):

    def list(self):
        client = self.server_groups_client
        sgs = client.list_server_groups()['server_groups']
        LOG.debug("List count, %s Server Groups", len(sgs))
        return sgs

    def delete(self):
        client = self.client
        sgs = self.list()
        for sg in sgs:
            try:
                client.delete_server_group(sg['id'])
            except Exception:
                LOG.exception("Delete Server Group exception.")

    def dry_run(self):
        sgs = self.list()
        self.data['server_groups'] = sgs


class KeyPairService(BaseService):
    def __init__(self, manager, **kwargs):
        super(KeyPairService, self).__init__(kwargs)
        self.client = manager.keypairs_client

    def list(self):
        client = self.client
        keypairs = client.list_keypairs()['keypairs']
        LOG.debug("List count, %s Keypairs", len(keypairs))
        return keypairs

    def delete(self):
        client = self.client
        keypairs = self.list()
        for k in keypairs:
            try:
                name = k['keypair']['name']
                client.delete_keypair(name)
            except Exception:
                LOG.exception("Delete Keypairs exception.")

    def dry_run(self):
        keypairs = self.list()
        self.data['keypairs'] = keypairs


class SecurityGroupService(BaseService):
    def __init__(self, manager, **kwargs):
        super(SecurityGroupService, self).__init__(kwargs)
        self.client = manager.compute_security_groups_client

    def list(self):
        client = self.client
        secgrps = client.list_security_groups()['security_groups']
        secgrp_del = [grp for grp in secgrps if grp['name'] != 'default']
        LOG.debug("List count, %s Security Groups", len(secgrp_del))
        return secgrp_del

    def delete(self):
        client = self.client
        secgrp_del = self.list()
        for g in secgrp_del:
            try:
                client.delete_security_group(g['id'])
            except Exception:
                LOG.exception("Delete Security Groups exception.")

    def dry_run(self):
        secgrp_del = self.list()
        self.data['security_groups'] = secgrp_del


class FloatingIpService(BaseService):
    def __init__(self, manager, **kwargs):
        super(FloatingIpService, self).__init__(kwargs)
        self.client = manager.compute_floating_ips_client

    def list(self):
        client = self.client
        floating_ips = client.list_floating_ips()['floating_ips']
        LOG.debug("List count, %s Floating IPs", len(floating_ips))
        return floating_ips

    def delete(self):
        client = self.client
        floating_ips = self.list()
        for f in floating_ips:
            try:
                client.delete_floating_ip(f['id'])
            except Exception:
                LOG.exception("Delete Floating IPs exception.")

    def dry_run(self):
        floating_ips = self.list()
        self.data['floating_ips'] = floating_ips


class VolumeService(BaseService):
    def __init__(self, manager, **kwargs):
        super(VolumeService, self).__init__(kwargs)
        self.client = manager.volumes_client_latest

    def list(self):
        client = self.client
        vols = client.list_volumes()['volumes']
        LOG.debug("List count, %s Volumes", len(vols))
        return vols

    def delete(self):
        client = self.client
        vols = self.list()
        for v in vols:
            try:
                client.delete_volume(v['id'])
            except Exception:
                LOG.exception("Delete Volume exception.")

    def dry_run(self):
        vols = self.list()
        self.data['volumes'] = vols


class VolumeQuotaService(BaseService):
    def __init__(self, manager, **kwargs):
        super(VolumeQuotaService, self).__init__(kwargs)
        self.client = manager.volume_quotas_v2_client

    def delete(self):
        client = self.client
        try:
            client.delete_quota_set(self.tenant_id)
        except Exception:
            LOG.exception("Delete Volume Quotas exception.")

    def dry_run(self):
        quotas = self.client.show_quota_set(
            self.tenant_id, params={'usage': True})['quota_set']
        self.data['volume_quotas'] = quotas


class NovaQuotaService(BaseService):
    def __init__(self, manager, **kwargs):
        super(NovaQuotaService, self).__init__(kwargs)
        self.client = manager.quotas_client
        self.limits_client = manager.limits_client

    def delete(self):
        client = self.client
        try:
            client.delete_quota_set(self.tenant_id)
        except Exception:
            LOG.exception("Delete Quotas exception.")

    def dry_run(self):
        client = self.limits_client
        quotas = client.show_limits()['limits']
        self.data['compute_quotas'] = quotas['absolute']


# Begin network service classes
class NetworkService(BaseService):
    def __init__(self, manager, **kwargs):
        super(NetworkService, self).__init__(kwargs)
        self.networks_client = manager.networks_client
        self.subnets_client = manager.subnets_client
        self.ports_client = manager.ports_client
        self.floating_ips_client = manager.floating_ips_client
        self.metering_labels_client = manager.metering_labels_client
        self.metering_label_rules_client = manager.metering_label_rules_client
        self.security_groups_client = manager.security_groups_client
        self.routers_client = manager.routers_client

    def _filter_by_conf_networks(self, item_list):
        if not item_list or not all(('network_id' in i for i in item_list)):
            return item_list

        return [item for item in item_list if item['network_id']
                not in CONF_NETWORKS]

    def list(self):
        client = self.networks_client
        networks = client.list_networks(**self.tenant_filter)
        networks = networks['networks']
        # filter out networks declared in tempest.conf
        if self.is_preserve:
            networks = [network for network in networks
                        if network['id'] not in CONF_NETWORKS]
        LOG.debug("List count, %s Networks", networks)
        return networks

    def delete(self):
        client = self.networks_client
        networks = self.list()
        for n in networks:
            try:
                client.delete_network(n['id'])
            except Exception:
                LOG.exception("Delete Network exception.")

    def dry_run(self):
        networks = self.list()
        self.data['networks'] = networks


class NetworkFloatingIpService(NetworkService):

    def list(self):
        client = self.floating_ips_client
        flips = client.list_floatingips(**self.tenant_filter)
        flips = flips['floatingips']
        LOG.debug("List count, %s Network Floating IPs", len(flips))
        return flips

    def delete(self):
        client = self.client
        flips = self.list()
        for flip in flips:
            try:
                client.delete_floatingip(flip['id'])
            except Exception:
                LOG.exception("Delete Network Floating IP exception.")

    def dry_run(self):
        flips = self.list()
        self.data['floating_ips'] = flips


class NetworkRouterService(NetworkService):

    def list(self):
        client = self.routers_client
        routers = client.list_routers(**self.tenant_filter)
        routers = routers['routers']
        if self.is_preserve:
            routers = [router for router in routers
                       if router['id'] != CONF_PUB_ROUTER]

        LOG.debug("List count, %s Routers", len(routers))
        return routers

    def delete(self):
        client = self.routers_client
        ports_client = self.ports_client
        routers = self.list()
        for router in routers:
            try:
                rid = router['id']
                ports = [port for port
                         in ports_client.list_ports(device_id=rid)['ports']
                         if net_info.is_router_interface_port(port)]
                for port in ports:
                    client.remove_router_interface(rid, port_id=port['id'])
                client.delete_router(rid)
            except Exception:
                LOG.exception("Delete Router exception.")

    def dry_run(self):
        routers = self.list()
        self.data['routers'] = routers


class NetworkHealthMonitorService(NetworkService):

    def list(self):
        client = self.client
        hms = client.list_health_monitors()
        hms = hms['health_monitors']
        hms = self._filter_by_tenant_id(hms)
        LOG.debug("List count, %s Health Monitors", len(hms))
        return hms

    def delete(self):
        client = self.client
        hms = self.list()
        for hm in hms:
            try:
                client.delete_health_monitor(hm['id'])
            except Exception:
                LOG.exception("Delete Health Monitor exception.")

    def dry_run(self):
        hms = self.list()
        self.data['health_monitors'] = hms


class NetworkMemberService(NetworkService):

    def list(self):
        client = self.client
        members = client.list_members()
        members = members['members']
        members = self._filter_by_tenant_id(members)
        LOG.debug("List count, %s Members", len(members))
        return members

    def delete(self):
        client = self.client
        members = self.list()
        for member in members:
            try:
                client.delete_member(member['id'])
            except Exception:
                LOG.exception("Delete Member exception.")

    def dry_run(self):
        members = self.list()
        self.data['members'] = members


class NetworkVipService(NetworkService):

    def list(self):
        client = self.client
        vips = client.list_vips()
        vips = vips['vips']
        vips = self._filter_by_tenant_id(vips)
        LOG.debug("List count, %s VIPs", len(vips))
        return vips

    def delete(self):
        client = self.client
        vips = self.list()
        for vip in vips:
            try:
                client.delete_vip(vip['id'])
            except Exception:
                LOG.exception("Delete VIP exception.")

    def dry_run(self):
        vips = self.list()
        self.data['vips'] = vips


class NetworkPoolService(NetworkService):

    def list(self):
        client = self.client
        pools = client.list_pools()
        pools = pools['pools']
        pools = self._filter_by_tenant_id(pools)
        LOG.debug("List count, %s Pools", len(pools))
        return pools

    def delete(self):
        client = self.client
        pools = self.list()
        for pool in pools:
            try:
                client.delete_pool(pool['id'])
            except Exception:
                LOG.exception("Delete Pool exception.")

    def dry_run(self):
        pools = self.list()
        self.data['pools'] = pools


class NetworkMeteringLabelRuleService(NetworkService):

    def list(self):
        client = self.metering_label_rules_client
        rules = client.list_metering_label_rules()
        rules = rules['metering_label_rules']
        rules = self._filter_by_tenant_id(rules)
        LOG.debug("List count, %s Metering Label Rules", len(rules))
        return rules

    def delete(self):
        client = self.metering_label_rules_client
        rules = self.list()
        for rule in rules:
            try:
                client.delete_metering_label_rule(rule['id'])
            except Exception:
                LOG.exception("Delete Metering Label Rule exception.")

    def dry_run(self):
        rules = self.list()
        self.data['rules'] = rules


class NetworkMeteringLabelService(NetworkService):

    def list(self):
        client = self.metering_labels_client
        labels = client.list_metering_labels()
        labels = labels['metering_labels']
        labels = self._filter_by_tenant_id(labels)
        LOG.debug("List count, %s Metering Labels", len(labels))
        return labels

    def delete(self):
        client = self.metering_labels_client
        labels = self.list()
        for label in labels:
            try:
                client.delete_metering_label(label['id'])
            except Exception:
                LOG.exception("Delete Metering Label exception.")

    def dry_run(self):
        labels = self.list()
        self.data['labels'] = labels


class NetworkPortService(NetworkService):

    def list(self):
        client = self.ports_client
        ports = [port for port in
                 client.list_ports(**self.tenant_filter)['ports']
                 if port["device_owner"] == "" or
                 port["device_owner"].startswith("compute:")]

        if self.is_preserve:
            ports = self._filter_by_conf_networks(ports)

        LOG.debug("List count, %s Ports", len(ports))
        return ports

    def delete(self):
        client = self.ports_client
        ports = self.list()
        for port in ports:
            try:
                client.delete_port(port['id'])
            except Exception:
                LOG.exception("Delete Port exception.")

    def dry_run(self):
        ports = self.list()
        self.data['ports'] = ports


class NetworkSecGroupService(NetworkService):
    def list(self):
        client = self.security_groups_client
        filter = self.tenant_filter
        # cannot delete default sec group so never show it.
        secgroups = [secgroup for secgroup in
                     client.list_security_groups(**filter)['security_groups']
                     if secgroup['name'] != 'default']

        if self.is_preserve:
            secgroups = self._filter_by_conf_networks(secgroups)
        LOG.debug("List count, %s security_groups", len(secgroups))
        return secgroups

    def delete(self):
        client = self.client
        secgroups = self.list()
        for secgroup in secgroups:
            try:
                client.delete_secgroup(secgroup['id'])
            except Exception:
                LOG.exception("Delete security_group exception.")

    def dry_run(self):
        secgroups = self.list()
        self.data['secgroups'] = secgroups


class NetworkSubnetService(NetworkService):

    def list(self):
        client = self.subnets_client
        subnets = client.list_subnets(**self.tenant_filter)
        subnets = subnets['subnets']
        if self.is_preserve:
            subnets = self._filter_by_conf_networks(subnets)
        LOG.debug("List count, %s Subnets", len(subnets))
        return subnets

    def delete(self):
        client = self.subnets_client
        subnets = self.list()
        for subnet in subnets:
            try:
                client.delete_subnet(subnet['id'])
            except Exception:
                LOG.exception("Delete Subnet exception.")

    def dry_run(self):
        subnets = self.list()
        self.data['subnets'] = subnets


# begin global services
class FlavorService(BaseService):
    def __init__(self, manager, **kwargs):
        super(FlavorService, self).__init__(kwargs)
        self.client = manager.flavors_client

    def list(self):
        client = self.client
        flavors = client.list_flavors({"is_public": None})['flavors']
        if not self.is_save_state:
            # recreate list removing saved flavors
            flavors = [flavor for flavor in flavors if flavor['id']
                       not in self.saved_state_json['flavors'].keys()]

        if self.is_preserve:
            flavors = [flavor for flavor in flavors
                       if flavor['id'] not in CONF_FLAVORS]
        LOG.debug("List count, %s Flavors after reconcile", len(flavors))
        return flavors

    def delete(self):
        client = self.client
        flavors = self.list()
        for flavor in flavors:
            try:
                client.delete_flavor(flavor['id'])
            except Exception:
                LOG.exception("Delete Flavor exception.")

    def dry_run(self):
        flavors = self.list()
        self.data['flavors'] = flavors

    def save_state(self):
        flavors = self.list()
        self.data['flavors'] = {}
        for flavor in flavors:
            self.data['flavors'][flavor['id']] = flavor['name']


class ImageService(BaseService):
    def __init__(self, manager, **kwargs):
        super(ImageService, self).__init__(kwargs)
        self.client = manager.compute_images_client

    def list(self):
        client = self.client
        images = client.list_images({"all_tenants": True})['images']
        if not self.is_save_state:
            images = [image for image in images if image['id']
                      not in self.saved_state_json['images'].keys()]
        if self.is_preserve:
            images = [image for image in images
                      if image['id'] not in CONF_IMAGES]
        LOG.debug("List count, %s Images after reconcile", len(images))
        return images

    def delete(self):
        client = self.client
        images = self.list()
        for image in images:
            try:
                client.delete_image(image['id'])
            except Exception:
                LOG.exception("Delete Image exception.")

    def dry_run(self):
        images = self.list()
        self.data['images'] = images

    def save_state(self):
        self.data['images'] = {}
        images = self.list()
        for image in images:
            self.data['images'][image['id']] = image['name']


class IdentityService(BaseService):
    def __init__(self, manager, **kwargs):
        super(IdentityService, self).__init__(kwargs)
        self.client = manager.identity_v3_client


class UserService(BaseService):

    def __init__(self, manager, **kwargs):
        super(UserService, self).__init__(kwargs)
        self.client = manager.users_v3_client

    def list(self):
        users = self.client.list_users()['users']

        if not self.is_save_state:
            users = [user for user in users if user['id']
                     not in self.saved_state_json['users'].keys()]

        if self.is_preserve:
            users = [user for user in users if user['name']
                     not in CONF_USERS]

        elif not self.is_save_state:  # Never delete admin user
            users = [user for user in users if user['name'] !=
                     CONF.auth.admin_username]

        LOG.debug("List count, %s Users after reconcile", len(users))
        return users

    def delete(self):
        users = self.list()
        for user in users:
            try:
                self.client.delete_user(user['id'])
            except Exception:
                LOG.exception("Delete User exception.")

    def dry_run(self):
        users = self.list()
        self.data['users'] = users

    def save_state(self):
        users = self.list()
        self.data['users'] = {}
        for user in users:
            self.data['users'][user['id']] = user['name']


class RoleService(BaseService):

    def __init__(self, manager, **kwargs):
        super(RoleService, self).__init__(kwargs)
        self.client = manager.roles_client

    def list(self):
        try:
            roles = self.client.list_roles()['roles']
            # reconcile roles with saved state and never list admin role
            if not self.is_save_state:
                roles = [role for role in roles if
                         (role['id'] not in
                          self.saved_state_json['roles'].keys()
                          and role['name'] != CONF.identity.admin_role)]
                LOG.debug("List count, %s Roles after reconcile", len(roles))
            return roles
        except Exception:
            LOG.exception("Cannot retrieve Roles.")
            return []

    def delete(self):
        roles = self.list()
        for role in roles:
            try:
                self.client.delete_role(role['id'])
            except Exception:
                LOG.exception("Delete Role exception.")

    def dry_run(self):
        roles = self.list()
        self.data['roles'] = roles

    def save_state(self):
        roles = self.list()
        self.data['roles'] = {}
        for role in roles:
            self.data['roles'][role['id']] = role['name']


class ProjectService(BaseService):

    def __init__(self, manager, **kwargs):
        super(ProjectService, self).__init__(kwargs)
        self.client = manager.projects_client

    def list(self):
        projects = self.client.list_projects()['projects']
        if not self.is_save_state:
            projects = [project for project in projects if (project['id']
                        not in self.saved_state_json['projects'].keys()
                        and project['name'] != CONF.auth.admin_project_name)]

        if self.is_preserve:
            projects = [project for project in projects if project['name']
                        not in CONF_PROJECTS]

        LOG.debug("List count, %s Projects after reconcile", len(projects))
        return projects

    def delete(self):
        projects = self.list()
        for project in projects:
            try:
                self.client.delete_project(project['id'])
            except Exception:
                LOG.exception("Delete project exception.")

    def dry_run(self):
        projects = self.list()
        self.data['projects'] = projects

    def save_state(self):
        projects = self.list()
        self.data['projects'] = {}
        for project in projects:
            self.data['projects'][project['id']] = project['name']


class DomainService(BaseService):

    def __init__(self, manager, **kwargs):
        super(DomainService, self).__init__(kwargs)
        self.client = manager.domains_client

    def list(self):
        client = self.client
        domains = client.list_domains()['domains']
        if not self.is_save_state:
            domains = [domain for domain in domains if domain['id']
                       not in self.saved_state_json['domains'].keys()]

        LOG.debug("List count, %s Domains after reconcile", len(domains))
        return domains

    def delete(self):
        client = self.client
        domains = self.list()
        for domain in domains:
            try:
                client.update_domain(domain['id'], enabled=False)
                client.delete_domain(domain['id'])
            except Exception:
                LOG.exception("Delete Domain exception.")

    def dry_run(self):
        domains = self.list()
        self.data['domains'] = domains

    def save_state(self):
        domains = self.list()
        self.data['domains'] = {}
        for domain in domains:
            self.data['domains'][domain['id']] = domain['name']


def get_project_cleanup_services():
    project_services = []
    # TODO(gmann): Tempest should provide some plugin hook for cleanup
    # script extension to plugin tests also.
    if IS_NOVA:
        project_services.append(ServerService)
        project_services.append(KeyPairService)
        project_services.append(SecurityGroupService)
        project_services.append(ServerGroupService)
        if not IS_NEUTRON:
            project_services.append(FloatingIpService)
        project_services.append(NovaQuotaService)
    if IS_NEUTRON:
        project_services.append(NetworkFloatingIpService)
        if utils.is_extension_enabled('metering', 'network'):
            project_services.append(NetworkMeteringLabelRuleService)
            project_services.append(NetworkMeteringLabelService)
        project_services.append(NetworkRouterService)
        project_services.append(NetworkPortService)
        project_services.append(NetworkSubnetService)
        project_services.append(NetworkService)
        project_services.append(NetworkSecGroupService)
    if IS_CINDER:
        project_services.append(SnapshotService)
        project_services.append(VolumeService)
        project_services.append(VolumeQuotaService)
    return project_services


def get_global_cleanup_services():
    global_services = []
    if IS_NOVA:
        global_services.append(FlavorService)
    if IS_GLANCE:
        global_services.append(ImageService)
    global_services.append(UserService)
    global_services.append(ProjectService)
    global_services.append(DomainService)
    global_services.append(RoleService)
    return global_services
