#!/usr/bin/env python

# Copyright 2014 Dell Inc.
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

from oslo_log import log as logging

from tempest import clients
from tempest import config
from tempest import test

LOG = logging.getLogger(__name__)
CONF = config.CONF

CONF_FLAVORS = None
CONF_IMAGES = None
CONF_NETWORKS = []
CONF_PRIV_NETWORK_NAME = None
CONF_PUB_NETWORK = None
CONF_PUB_ROUTER = None
CONF_TENANTS = None
CONF_USERS = None

IS_CEILOMETER = None
IS_CINDER = None
IS_GLANCE = None
IS_HEAT = None
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
    global CONF_TENANTS
    global CONF_USERS
    global IS_CEILOMETER
    global IS_CINDER
    global IS_GLANCE
    global IS_HEAT
    global IS_NEUTRON
    global IS_NOVA

    IS_CEILOMETER = CONF.service_available.ceilometer
    IS_CINDER = CONF.service_available.cinder
    IS_GLANCE = CONF.service_available.glance
    IS_HEAT = CONF.service_available.heat
    IS_NEUTRON = CONF.service_available.neutron
    IS_NOVA = CONF.service_available.nova

    CONF_FLAVORS = [CONF.compute.flavor_ref, CONF.compute.flavor_ref_alt]
    CONF_IMAGES = [CONF.compute.image_ref, CONF.compute.image_ref_alt]
    CONF_PRIV_NETWORK_NAME = CONF.compute.fixed_network_name
    CONF_PUB_NETWORK = CONF.network.public_network_id
    CONF_PUB_ROUTER = CONF.network.public_router_id
    CONF_TENANTS = [CONF.identity.admin_tenant_name,
                    CONF.identity.tenant_name,
                    CONF.identity.alt_tenant_name]
    CONF_USERS = [CONF.identity.admin_username, CONF.identity.username,
                  CONF.identity.alt_username]

    if IS_NEUTRON:
        CONF_PRIV_NETWORK = _get_priv_net_id(CONF.compute.fixed_network_name,
                                             CONF.identity.tenant_name)
        CONF_NETWORKS = [CONF_PUB_NETWORK, CONF_PRIV_NETWORK]


def _get_priv_net_id(prv_net_name, tenant_name):
    am = clients.AdminManager()
    net_cl = am.network_client
    id_cl = am.identity_client

    networks = net_cl.list_networks()
    tenant = id_cl.get_tenant_by_name(tenant_name)
    t_id = tenant['id']
    n_id = None
    for net in networks['networks']:
        if (net['tenant_id'] == t_id and net['name'] == prv_net_name):
            n_id = net['id']
            break
    return n_id


class BaseService(object):
    def __init__(self, kwargs):
        self.client = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _filter_by_tenant_id(self, item_list):
        if (item_list is None
                or len(item_list) == 0
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
        self.client = manager.snapshots_client

    def list(self):
        client = self.client
        snaps = client.list_snapshots()
        LOG.debug("List count, %s Snapshots" % len(snaps))
        return snaps

    def delete(self):
        snaps = self.list()
        client = self.client
        for snap in snaps:
            try:
                client.delete_snapshot(snap['id'])
            except Exception as e:
                LOG.exception("Delete Snapshot exception: %s" % e)
                pass

    def dry_run(self):
        snaps = self.list()
        self.data['snapshots'] = snaps


class ServerService(BaseService):
    def __init__(self, manager, **kwargs):
        super(ServerService, self).__init__(kwargs)
        self.client = manager.servers_client

    def list(self):
        client = self.client
        servers_body = client.list_servers()
        servers = servers_body['servers']
        LOG.debug("List count, %s Servers" % len(servers))
        return servers

    def delete(self):
        client = self.client
        servers = self.list()
        for server in servers:
            try:
                client.delete_server(server['id'])
            except Exception as e:
                LOG.exception("Delete Server exception: %s" % e)
                pass

    def dry_run(self):
        servers = self.list()
        self.data['servers'] = servers


class ServerGroupService(ServerService):

    def list(self):
        client = self.client
        sgs = client.list_server_groups()
        LOG.debug("List count, %s Server Groups" % len(sgs))
        return sgs

    def delete(self):
        client = self.client
        sgs = self.list()
        for sg in sgs:
            try:
                client.delete_server_group(sg['id'])
            except Exception as e:
                LOG.exception("Delete Server Group exception: %s" % e)
                pass

    def dry_run(self):
        sgs = self.list()
        self.data['server_groups'] = sgs


class StackService(BaseService):
    def __init__(self, manager, **kwargs):
        super(StackService, self).__init__(kwargs)
        self.client = manager.orchestration_client

    def list(self):
        client = self.client
        stacks = client.list_stacks()
        LOG.debug("List count, %s Stacks" % len(stacks))
        return stacks

    def delete(self):
        client = self.client
        stacks = self.list()
        for stack in stacks:
            try:
                client.delete_stack(stack['id'])
            except Exception as e:
                LOG.exception("Delete Stack exception: %s " % e)
                pass

    def dry_run(self):
        stacks = self.list()
        self.data['stacks'] = stacks


class KeyPairService(BaseService):
    def __init__(self, manager, **kwargs):
        super(KeyPairService, self).__init__(kwargs)
        self.client = manager.keypairs_client

    def list(self):
        client = self.client
        keypairs = client.list_keypairs()
        LOG.debug("List count, %s Keypairs" % len(keypairs))
        return keypairs

    def delete(self):
        client = self.client
        keypairs = self.list()
        for k in keypairs:
            try:
                name = k['keypair']['name']
                client.delete_keypair(name)
            except Exception as e:
                LOG.exception("Delete Keypairs exception: %s" % e)
                pass

    def dry_run(self):
        keypairs = self.list()
        self.data['keypairs'] = keypairs


class SecurityGroupService(BaseService):
    def __init__(self, manager, **kwargs):
        super(SecurityGroupService, self).__init__(kwargs)
        self.client = manager.security_groups_client

    def list(self):
        client = self.client
        secgrps = client.list_security_groups()
        secgrp_del = [grp for grp in secgrps if grp['name'] != 'default']
        LOG.debug("List count, %s Security Groups" % len(secgrp_del))
        return secgrp_del

    def delete(self):
        client = self.client
        secgrp_del = self.list()
        for g in secgrp_del:
            try:
                client.delete_security_group(g['id'])
            except Exception as e:
                LOG.exception("Delete Security Groups exception: %s" % e)

    def dry_run(self):
        secgrp_del = self.list()
        self.data['security_groups'] = secgrp_del


class FloatingIpService(BaseService):
    def __init__(self, manager, **kwargs):
        super(FloatingIpService, self).__init__(kwargs)
        self.client = manager.floating_ips_client

    def list(self):
        client = self.client
        floating_ips = client.list_floating_ips()
        LOG.debug("List count, %s Floating IPs" % len(floating_ips))
        return floating_ips

    def delete(self):
        client = self.client
        floating_ips = self.list()
        for f in floating_ips:
            try:
                client.delete_floating_ip(f['id'])
            except Exception as e:
                LOG.exception("Delete Floating IPs exception: %s" % e)
                pass

    def dry_run(self):
        floating_ips = self.list()
        self.data['floating_ips'] = floating_ips


class VolumeService(BaseService):
    def __init__(self, manager, **kwargs):
        super(VolumeService, self).__init__(kwargs)
        self.client = manager.volumes_client

    def list(self):
        client = self.client
        vols = client.list_volumes()
        LOG.debug("List count, %s Volumes" % len(vols))
        return vols

    def delete(self):
        client = self.client
        vols = self.list()
        for v in vols:
            try:
                client.delete_volume(v['id'])
            except Exception as e:
                LOG.exception("Delete Volume exception: %s" % e)
                pass

    def dry_run(self):
        vols = self.list()
        self.data['volumes'] = vols


# Begin network service classes
class NetworkService(BaseService):
    def __init__(self, manager, **kwargs):
        super(NetworkService, self).__init__(kwargs)
        self.client = manager.network_client

    def _filter_by_conf_networks(self, item_list):
        if not item_list or not all(('network_id' in i for i in item_list)):
            return item_list

        return [item for item in item_list if item['network_id']
                not in CONF_NETWORKS]

    def list(self):
        client = self.client
        networks = client.list_networks()
        networks = self._filter_by_tenant_id(networks['networks'])
        # filter out networks declared in tempest.conf
        if self.is_preserve:
            networks = [network for network in networks
                        if network['id'] not in CONF_NETWORKS]
        LOG.debug("List count, %s Networks" % networks)
        return networks

    def delete(self):
        client = self.client
        networks = self.list()
        for n in networks:
            try:
                client.delete_network(n['id'])
            except Exception as e:
                LOG.exception("Delete Network exception: %s" % e)
                pass

    def dry_run(self):
        networks = self.list()
        self.data['networks'] = networks


class NetworkIpSecPolicyService(NetworkService):

    def list(self):
        client = self.client
        ipsecpols = client.list_ipsecpolicies()
        ipsecpols = ipsecpols['ipsecpolicies']
        ipsecpols = self._filter_by_tenant_id(ipsecpols)
        LOG.debug("List count, %s IP Security Policies" % len(ipsecpols))
        return ipsecpols

    def delete(self):
        client = self.client
        ipsecpols = self.list()
        for ipsecpol in ipsecpols:
            try:
                client.delete_ipsecpolicy(ipsecpol['id'])
            except Exception as e:
                LOG.exception("Delete IP Securty Policy exception: %s" % e)
                pass

    def dry_run(self):
        ipsecpols = self.list()
        self.data['ip_security_policies'] = ipsecpols


class NetworkFwPolicyService(NetworkService):

    def list(self):
        client = self.client
        fwpols = client.list_firewall_policies()
        fwpols = fwpols['firewall_policies']
        fwpols = self._filter_by_tenant_id(fwpols)
        LOG.debug("List count, %s Firewall Policies" % len(fwpols))
        return fwpols

    def delete(self):
        client = self.client
        fwpols = self.list()
        for fwpol in fwpols:
            try:
                client.delete_firewall_policy(fwpol['id'])
            except Exception as e:
                LOG.exception("Delete Firewall Policy exception: %s" % e)
                pass

    def dry_run(self):
        fwpols = self.list()
        self.data['firewall_policies'] = fwpols


class NetworkFwRulesService(NetworkService):

    def list(self):
        client = self.client
        fwrules = client.list_firewall_rules()
        fwrules = fwrules['firewall_rules']
        fwrules = self._filter_by_tenant_id(fwrules)
        LOG.debug("List count, %s Firewall Rules" % len(fwrules))
        return fwrules

    def delete(self):
        client = self.client
        fwrules = self.list()
        for fwrule in fwrules:
            try:
                client.delete_firewall_rule(fwrule['id'])
            except Exception as e:
                LOG.exception("Delete Firewall Rule exception: %s" % e)
                pass

    def dry_run(self):
        fwrules = self.list()
        self.data['firewall_rules'] = fwrules


class NetworkIkePolicyService(NetworkService):

    def list(self):
        client = self.client
        ikepols = client.list_ikepolicies()
        ikepols = ikepols['ikepolicies']
        ikepols = self._filter_by_tenant_id(ikepols)
        LOG.debug("List count, %s IKE Policies" % len(ikepols))
        return ikepols

    def delete(self):
        client = self.client
        ikepols = self.list()
        for ikepol in ikepols:
            try:
                client.delete_firewall_rule(ikepol['id'])
            except Exception as e:
                LOG.exception("Delete IKE Policy exception: %s" % e)
                pass

    def dry_run(self):
        ikepols = self.list()
        self.data['ike_policies'] = ikepols


class NetworkVpnServiceService(NetworkService):

    def list(self):
        client = self.client
        vpnsrvs = client.list_vpnservices()
        vpnsrvs = vpnsrvs['vpnservices']
        vpnsrvs = self._filter_by_tenant_id(vpnsrvs)
        LOG.debug("List count, %s VPN Services" % len(vpnsrvs))
        return vpnsrvs

    def delete(self):
        client = self.client
        vpnsrvs = self.list()
        for vpnsrv in vpnsrvs:
            try:
                client.delete_vpnservice(vpnsrv['id'])
            except Exception as e:
                LOG.exception("Delete VPN Service exception: %s" % e)
                pass

    def dry_run(self):
        vpnsrvs = self.list()
        self.data['vpn_services'] = vpnsrvs


class NetworkFloatingIpService(NetworkService):

    def list(self):
        client = self.client
        flips = client.list_floatingips()
        flips = flips['floatingips']
        flips = self._filter_by_tenant_id(flips)
        LOG.debug("List count, %s Network Floating IPs" % len(flips))
        return flips

    def delete(self):
        client = self.client
        flips = self.list()
        for flip in flips:
            try:
                client.delete_floatingip(flip['id'])
            except Exception as e:
                LOG.exception("Delete Network Floating IP exception: %s" % e)
                pass

    def dry_run(self):
        flips = self.list()
        self.data['floating_ips'] = flips


class NetworkRouterService(NetworkService):

    def list(self):
        client = self.client
        routers = client.list_routers()
        routers = routers['routers']
        routers = self._filter_by_tenant_id(routers)
        if self.is_preserve:
            routers = [router for router in routers
                       if router['id'] != CONF_PUB_ROUTER]

        LOG.debug("List count, %s Routers" % len(routers))
        return routers

    def delete(self):
        client = self.client
        routers = self.list()
        for router in routers:
            try:
                rid = router['id']
                ports = client.list_router_interfaces(rid)
                ports = ports['ports']
                for port in ports:
                    subid = port['fixed_ips'][0]['subnet_id']
                    client.remove_router_interface_with_subnet_id(rid, subid)
                client.delete_router(rid)
            except Exception as e:
                LOG.exception("Delete Router exception: %s" % e)
                pass

    def dry_run(self):
        routers = self.list()
        self.data['routers'] = routers


class NetworkHealthMonitorService(NetworkService):

    def list(self):
        client = self.client
        hms = client.list_health_monitors()
        hms = hms['health_monitors']
        hms = self._filter_by_tenant_id(hms)
        LOG.debug("List count, %s Health Monitors" % len(hms))
        return hms

    def delete(self):
        client = self.client
        hms = self.list()
        for hm in hms:
            try:
                client.delete_health_monitor(hm['id'])
            except Exception as e:
                LOG.exception("Delete Health Monitor exception: %s" % e)
                pass

    def dry_run(self):
        hms = self.list()
        self.data['health_monitors'] = hms


class NetworkMemberService(NetworkService):

    def list(self):
        client = self.client
        members = client.list_members()
        members = members['members']
        members = self._filter_by_tenant_id(members)
        LOG.debug("List count, %s Members" % len(members))
        return members

    def delete(self):
        client = self.client
        members = self.list()
        for member in members:
            try:
                client.delete_member(member['id'])
            except Exception as e:
                LOG.exception("Delete Member exception: %s" % e)
                pass

    def dry_run(self):
        members = self.list()
        self.data['members'] = members


class NetworkVipService(NetworkService):

    def list(self):
        client = self.client
        vips = client.list_vips()
        vips = vips['vips']
        vips = self._filter_by_tenant_id(vips)
        LOG.debug("List count, %s VIPs" % len(vips))
        return vips

    def delete(self):
        client = self.client
        vips = self.list()
        for vip in vips:
            try:
                client.delete_vip(vip['id'])
            except Exception as e:
                LOG.exception("Delete VIP exception: %s" % e)
                pass

    def dry_run(self):
        vips = self.list()
        self.data['vips'] = vips


class NetworkPoolService(NetworkService):

    def list(self):
        client = self.client
        pools = client.list_pools()
        pools = pools['pools']
        pools = self._filter_by_tenant_id(pools)
        LOG.debug("List count, %s Pools" % len(pools))
        return pools

    def delete(self):
        client = self.client
        pools = self.list()
        for pool in pools:
            try:
                client.delete_pool(pool['id'])
            except Exception as e:
                LOG.exception("Delete Pool exception: %s" % e)
                pass

    def dry_run(self):
        pools = self.list()
        self.data['pools'] = pools


class NetworMeteringLabelRuleService(NetworkService):

    def list(self):
        client = self.client
        rules = client.list_metering_label_rules()
        rules = rules['metering_label_rules']
        rules = self._filter_by_tenant_id(rules)
        LOG.debug("List count, %s Metering Label Rules" % len(rules))
        return rules

    def delete(self):
        client = self.client
        rules = self.list()
        for rule in rules:
            try:
                client.delete_metering_label_rule(rule['id'])
            except Exception as e:
                LOG.exception("Delete Metering Label Rule exception: %s" % e)
                pass

    def dry_run(self):
        rules = self.list()
        self.data['rules'] = rules


class NetworMeteringLabelService(NetworkService):

    def list(self):
        client = self.client
        labels = client.list_metering_labels()
        labels = labels['metering_labels']
        labels = self._filter_by_tenant_id(labels)
        LOG.debug("List count, %s Metering Labels" % len(labels))
        return labels

    def delete(self):
        client = self.client
        labels = self.list()
        for label in labels:
            try:
                client.delete_metering_label(label['id'])
            except Exception as e:
                LOG.exception("Delete Metering Label exception: %s" % e)
                pass

    def dry_run(self):
        labels = self.list()
        self.data['labels'] = labels


class NetworkPortService(NetworkService):

    def list(self):
        client = self.client
        ports = client.list_ports()
        ports = ports['ports']
        ports = self._filter_by_tenant_id(ports)
        if self.is_preserve:
            ports = self._filter_by_conf_networks(ports)
        LOG.debug("List count, %s Ports" % len(ports))
        return ports

    def delete(self):
        client = self.client
        ports = self.list()
        for port in ports:
            try:
                client.delete_port(port['id'])
            except Exception as e:
                LOG.exception("Delete Port exception: %s" % e)
                pass

    def dry_run(self):
        ports = self.list()
        self.data['ports'] = ports


class NetworkSubnetService(NetworkService):

    def list(self):
        client = self.client
        subnets = client.list_subnets()
        subnets = subnets['subnets']
        subnets = self._filter_by_tenant_id(subnets)
        if self.is_preserve:
            subnets = self._filter_by_conf_networks(subnets)
        LOG.debug("List count, %s Subnets" % len(subnets))
        return subnets

    def delete(self):
        client = self.client
        subnets = self.list()
        for subnet in subnets:
            try:
                client.delete_subnet(subnet['id'])
            except Exception as e:
                LOG.exception("Delete Subnet exception: %s" % e)
                pass

    def dry_run(self):
        subnets = self.list()
        self.data['subnets'] = subnets


# Telemetry services
class TelemetryAlarmService(BaseService):
    def __init__(self, manager, **kwargs):
        super(TelemetryAlarmService, self).__init__(kwargs)
        self.client = manager.telemetry_client

    def list(self):
        client = self.client
        alarms = client.list_alarms()
        LOG.debug("List count, %s Alarms" % len(alarms))
        return alarms

    def delete(self):
        client = self.client
        alarms = self.list()
        for alarm in alarms:
            try:
                client.delete_alarm(alarm['id'])
            except Exception as e:
                LOG.exception("Delete Alarms exception: %s" % e)
                pass

    def dry_run(self):
        alarms = self.list()
        self.data['alarms'] = alarms


# begin global services
class FlavorService(BaseService):
    def __init__(self, manager, **kwargs):
        super(FlavorService, self).__init__(kwargs)
        self.client = manager.flavors_client

    def list(self):
        client = self.client
        flavors = client.list_flavors({"is_public": None})
        if not self.is_save_state:
            # recreate list removing saved flavors
            flavors = [flavor for flavor in flavors if flavor['id']
                       not in self.saved_state_json['flavors'].keys()]

        if self.is_preserve:
            flavors = [flavor for flavor in flavors
                       if flavor['id'] not in CONF_FLAVORS]
        LOG.debug("List count, %s Flavors after reconcile" % len(flavors))
        return flavors

    def delete(self):
        client = self.client
        flavors = self.list()
        for flavor in flavors:
            try:
                client.delete_flavor(flavor['id'])
            except Exception as e:
                LOG.exception("Delete Flavor exception: %s" % e)
                pass

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
        self.client = manager.images_client

    def list(self):
        client = self.client
        images = client.list_images({"all_tenants": True})
        if not self.is_save_state:
            images = [image for image in images if image['id']
                      not in self.saved_state_json['images'].keys()]
        if self.is_preserve:
            images = [image for image in images
                      if image['id'] not in CONF_IMAGES]
        LOG.debug("List count, %s Images after reconcile" % len(images))
        return images

    def delete(self):
        client = self.client
        images = self.list()
        for image in images:
            try:
                client.delete_image(image['id'])
            except Exception as e:
                LOG.exception("Delete Image exception: %s" % e)
                pass

    def dry_run(self):
        images = self.list()
        self.data['images'] = images

    def save_state(self):
        images = self.list()
        self.data['images'] = {}
        for image in images:
            self.data['images'][image['id']] = image['name']


class IdentityService(BaseService):
    def __init__(self, manager, **kwargs):
        super(IdentityService, self).__init__(kwargs)
        self.client = manager.identity_client


class UserService(IdentityService):

    def list(self):
        client = self.client
        users = client.get_users()

        if not self.is_save_state:
            users = [user for user in users if user['id']
                     not in self.saved_state_json['users'].keys()]

        if self.is_preserve:
            users = [user for user in users if user['name']
                     not in CONF_USERS]

        elif not self.is_save_state:  # Never delete admin user
            users = [user for user in users if user['name'] !=
                     CONF.identity.admin_username]

        LOG.debug("List count, %s Users after reconcile" % len(users))
        return users

    def delete(self):
        client = self.client
        users = self.list()
        for user in users:
            try:
                client.delete_user(user['id'])
            except Exception as e:
                LOG.exception("Delete User exception: %s" % e)
                pass

    def dry_run(self):
        users = self.list()
        self.data['users'] = users

    def save_state(self):
        users = self.list()
        self.data['users'] = {}
        for user in users:
            self.data['users'][user['id']] = user['name']


class RoleService(IdentityService):

    def list(self):
        client = self.client
        try:
            roles = client.list_roles()
            # reconcile roles with saved state and never list admin role
            if not self.is_save_state:
                roles = [role for role in roles if
                         (role['id'] not in
                          self.saved_state_json['roles'].keys()
                          and role['name'] != CONF.identity.admin_role)]
                LOG.debug("List count, %s Roles after reconcile" % len(roles))
            return roles
        except Exception as ex:
            LOG.exception("Cannot retrieve Roles, exception: %s" % ex)
            return []

    def delete(self):
        client = self.client
        roles = self.list()
        for role in roles:
            try:
                client.delete_role(role['id'])
            except Exception as e:
                LOG.exception("Delete Role exception: %s" % e)
                pass

    def dry_run(self):
        roles = self.list()
        self.data['roles'] = roles

    def save_state(self):
        roles = self.list()
        self.data['roles'] = {}
        for role in roles:
            self.data['roles'][role['id']] = role['name']


class TenantService(IdentityService):

    def list(self):
        client = self.client
        tenants = client.list_tenants()
        if not self.is_save_state:
            tenants = [tenant for tenant in tenants if (tenant['id']
                       not in self.saved_state_json['tenants'].keys()
                       and tenant['name'] != CONF.identity.admin_tenant_name)]

        if self.is_preserve:
            tenants = [tenant for tenant in tenants if tenant['name']
                       not in CONF_TENANTS]

        LOG.debug("List count, %s Tenants after reconcile" % len(tenants))
        return tenants

    def delete(self):
        client = self.client
        tenants = self.list()
        for tenant in tenants:
            try:
                client.delete_tenant(tenant['id'])
            except Exception as e:
                LOG.exception("Delete Tenant exception: %s" % e)
                pass

    def dry_run(self):
        tenants = self.list()
        self.data['tenants'] = tenants

    def save_state(self):
        tenants = self.list()
        self.data['tenants'] = {}
        for tenant in tenants:
            self.data['tenants'][tenant['id']] = tenant['name']


class DomainService(BaseService):

    def __init__(self, manager, **kwargs):
        super(DomainService, self).__init__(kwargs)
        self.client = manager.identity_v3_client

    def list(self):
        client = self.client
        domains = client.list_domains()
        if not self.is_save_state:
            domains = [domain for domain in domains if domain['id']
                       not in self.saved_state_json['domains'].keys()]

        LOG.debug("List count, %s Domains after reconcile" % len(domains))
        return domains

    def delete(self):
        client = self.client
        domains = self.list()
        for domain in domains:
            try:
                client.update_domain(domain['id'], enabled=False)
                client.delete_domain(domain['id'])
            except Exception as e:
                LOG.exception("Delete Domain exception: %s" % e)
                pass

    def dry_run(self):
        domains = self.list()
        self.data['domains'] = domains

    def save_state(self):
        domains = self.list()
        self.data['domains'] = {}
        for domain in domains:
            self.data['domains'][domain['id']] = domain['name']


def get_tenant_cleanup_services():
    tenant_services = []

    if IS_CEILOMETER:
        tenant_services.append(TelemetryAlarmService)
    if IS_NOVA:
        tenant_services.append(ServerService)
        tenant_services.append(KeyPairService)
        tenant_services.append(SecurityGroupService)
        tenant_services.append(ServerGroupService)
        if not IS_NEUTRON:
            tenant_services.append(FloatingIpService)
    if IS_HEAT:
        tenant_services.append(StackService)
    if IS_NEUTRON:
        if test.is_extension_enabled('vpnaas', 'network'):
            tenant_services.append(NetworkIpSecPolicyService)
            tenant_services.append(NetworkIkePolicyService)
            tenant_services.append(NetworkVpnServiceService)
        if test.is_extension_enabled('fwaas', 'network'):
            tenant_services.append(NetworkFwPolicyService)
            tenant_services.append(NetworkFwRulesService)
        if test.is_extension_enabled('lbaas', 'network'):
            tenant_services.append(NetworkHealthMonitorService)
            tenant_services.append(NetworkMemberService)
            tenant_services.append(NetworkVipService)
            tenant_services.append(NetworkPoolService)
        if test.is_extension_enabled('metering', 'network'):
            tenant_services.append(NetworMeteringLabelRuleService)
            tenant_services.append(NetworMeteringLabelService)
        tenant_services.append(NetworkRouterService)
        tenant_services.append(NetworkFloatingIpService)
        tenant_services.append(NetworkPortService)
        tenant_services.append(NetworkSubnetService)
        tenant_services.append(NetworkService)
    if IS_CINDER:
        tenant_services.append(SnapshotService)
        tenant_services.append(VolumeService)
    return tenant_services


def get_global_cleanup_services():
    global_services = []
    if IS_NOVA:
        global_services.append(FlavorService)
    if IS_GLANCE:
        global_services.append(ImageService)
    global_services.append(UserService)
    global_services.append(TenantService)
    global_services.append(DomainService)
    global_services.append(RoleService)
    return global_services
