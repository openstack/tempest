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

from urllib import parse as urllib

from oslo_log import log as logging

from tempest import clients
from tempest.common import credentials_factory as credentials
from tempest.common import identity
from tempest.common import utils
from tempest.common.utils import net_info
from tempest import config
from tempest.lib import exceptions

LOG = logging.getLogger('tempest.cmd.cleanup')
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
            self.tenant_filter['project_id'] = self.tenant_id

    def _filter_by_tenant_id(self, item_list):
        if (item_list is None or
                not item_list or
                not hasattr(self, 'tenant_id') or
                self.tenant_id is None or
                'tenant_id' not in item_list[0]):
            return item_list

        return [item for item in item_list
                if item['tenant_id'] == self.tenant_id]

    def _filter_by_prefix(self, item_list, top_key=None):
        items = []
        for item in item_list:
            name = item[top_key]['name'] if top_key else item['name']
            if name.startswith(self.prefix):
                items.append(item)
        return items

    def _filter_by_resource_list(self, item_list, attr):
        if attr not in self.resource_list_json:
            return []
        items = []
        for item in item_list:
            item_id = (item['keypair']['name'] if attr == 'keypairs'
                       else item['id'])
            if item_id in self.resource_list_json[attr].keys():
                items.append(item)
        return items

    def _filter_out_ids_from_saved(self, item_list, attr):
        items = []
        for item in item_list:
            item_id = (item['keypair']['name'] if attr == 'keypairs'
                       else item['id'])
            if item_id not in self.saved_state_json[attr].keys():
                items.append(item)
        return items

    def list(self):
        pass

    def delete(self):
        pass

    def dry_run(self):
        pass

    def save_state(self):
        pass

    def run(self):
        try:
            if self.is_dry_run:
                self.dry_run()
            elif self.is_save_state:
                self.save_state()
            else:
                self.delete()
        except exceptions.NotImplemented as exc:
            # Many OpenStack services use extensions logic to implement the
            # features or resources. Tempest cleanup tries to clean up the test
            # resources without having much logic of extensions checks etc.
            # If any of the extension is missing then, service will return
            # NotImplemented error.
            msg = ("Got NotImplemented error in %s, full exception: %s" %
                   (str(self.__class__), str(exc)))
            LOG.exception(msg)
            self.got_exceptions.append(exc)


class SnapshotService(BaseService):

    def __init__(self, manager, **kwargs):
        super(SnapshotService, self).__init__(kwargs)
        self.client = manager.snapshots_client_latest

    def list(self):
        client = self.client
        snaps = client.list_snapshots()['snapshots']

        if self.prefix:
            snaps = self._filter_by_prefix(snaps)
        elif self.is_resource_list:
            snaps = self._filter_by_resource_list(snaps, 'snapshots')
        elif not self.is_save_state:
            # recreate list removing saved snapshots
            snaps = self._filter_out_ids_from_saved(snaps, 'snapshots')
        LOG.debug("List count, %s Snapshots", len(snaps))
        return snaps

    def delete(self):
        snaps = self.list()
        client = self.client
        for snap in snaps:
            try:
                LOG.debug("Deleting Snapshot with id %s", snap['id'])
                client.delete_snapshot(snap['id'])
            except Exception:
                LOG.exception("Delete Snapshot %s exception.", snap['id'])

    def dry_run(self):
        snaps = self.list()
        self.data['snapshots'] = snaps

    def save_state(self):
        snaps = self.list()
        self.data['snapshots'] = {}
        for snap in snaps:
            self.data['snapshots'][snap['id']] = snap['name']


class ServerService(BaseService):
    def __init__(self, manager, **kwargs):
        super(ServerService, self).__init__(kwargs)
        self.client = manager.servers_client
        self.server_groups_client = manager.server_groups_client

    def list(self):
        client = self.client
        servers_body = client.list_servers()
        servers = servers_body['servers']

        if self.prefix:
            servers = self._filter_by_prefix(servers)
        elif self.is_resource_list:
            servers = self._filter_by_resource_list(servers, 'servers')
        elif not self.is_save_state:
            # recreate list removing saved servers
            servers = self._filter_out_ids_from_saved(servers, 'servers')
        LOG.debug("List count, %s Servers", len(servers))
        return servers

    def delete(self):
        client = self.client
        servers = self.list()
        for server in servers:
            try:
                LOG.debug("Deleting Server with id %s", server['id'])
                client.delete_server(server['id'])
            except Exception:
                LOG.exception("Delete Server %s exception.", server['id'])

    def dry_run(self):
        servers = self.list()
        self.data['servers'] = servers

    def save_state(self):
        servers = self.list()
        self.data['servers'] = {}
        for server in servers:
            self.data['servers'][server['id']] = server['name']


class ServerGroupService(ServerService):

    def list(self):
        client = self.server_groups_client
        sgs = client.list_server_groups(all_projects=True)['server_groups']

        if self.prefix:
            sgs = self._filter_by_prefix(sgs)
        elif self.is_resource_list:
            sgs = self._filter_by_resource_list(sgs, 'server_groups')
        elif not self.is_save_state:
            # recreate list removing saved server_groups
            sgs = self._filter_out_ids_from_saved(sgs, 'server_groups')
        LOG.debug("List count, %s Server Groups", len(sgs))
        return sgs

    def delete(self):
        client = self.server_groups_client
        sgs = self.list()
        for sg in sgs:
            try:
                LOG.debug("Deleting Server Group with id %s", sg['id'])
                client.delete_server_group(sg['id'])
            except Exception:
                LOG.exception("Delete Server Group %s exception.", sg['id'])

    def dry_run(self):
        sgs = self.list()
        self.data['server_groups'] = sgs

    def save_state(self):
        sgs = self.list()
        self.data['server_groups'] = {}
        for sg in sgs:
            self.data['server_groups'][sg['id']] = sg['name']


class KeyPairService(BaseService):
    def __init__(self, manager, **kwargs):
        super(KeyPairService, self).__init__(kwargs)
        self.client = manager.keypairs_client

    def list(self):
        client = self.client
        keypairs = client.list_keypairs()['keypairs']

        if self.prefix:
            keypairs = self._filter_by_prefix(keypairs, 'keypair')
        elif self.is_resource_list:
            keypairs = self._filter_by_resource_list(keypairs, 'keypairs')
        elif not self.is_save_state:
            keypairs = self._filter_out_ids_from_saved(keypairs, 'keypairs')
        LOG.debug("List count, %s Keypairs", len(keypairs))
        return keypairs

    def delete(self):
        client = self.client
        keypairs = self.list()
        for k in keypairs:
            name = k['keypair']['name']
            try:
                LOG.debug("Deleting keypair %s", name)
                client.delete_keypair(name)
            except Exception:
                LOG.exception("Delete Keypair %s exception.", name)

    def dry_run(self):
        keypairs = self.list()
        self.data['keypairs'] = keypairs

    def save_state(self):
        keypairs = self.list()
        self.data['keypairs'] = {}
        for keypair in keypairs:
            keypair = keypair['keypair']
            self.data['keypairs'][keypair['name']] = keypair


class VolumeService(BaseService):
    def __init__(self, manager, **kwargs):
        super(VolumeService, self).__init__(kwargs)
        self.client = manager.volumes_client_latest

    def list(self):
        client = self.client
        vols = client.list_volumes()['volumes']

        if self.prefix:
            vols = self._filter_by_prefix(vols)
        elif self.is_resource_list:
            vols = self._filter_by_resource_list(vols, 'volumes')
        elif not self.is_save_state:
            # recreate list removing saved volumes
            vols = self._filter_out_ids_from_saved(vols, 'volumes')
        LOG.debug("List count, %s Volumes", len(vols))
        return vols

    def delete(self):
        client = self.client
        vols = self.list()
        for v in vols:
            try:
                LOG.debug("Deleting volume with id %s", v['id'])
                client.delete_volume(v['id'])
            except Exception:
                LOG.exception("Delete Volume %s exception.", v['id'])

    def dry_run(self):
        vols = self.list()
        self.data['volumes'] = vols

    def save_state(self):
        vols = self.list()
        self.data['volumes'] = {}
        for vol in vols:
            self.data['volumes'][vol['id']] = vol['name']


class VolumeQuotaService(BaseService):
    def __init__(self, manager, **kwargs):
        super(VolumeQuotaService, self).__init__(kwargs)
        self.client = manager.volume_quotas_client_latest

    def delete(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        client = self.client
        try:
            LOG.debug("Deleting Volume Quotas for project with id %s",
                      self.project_id)
            client.delete_quota_set(self.project_id)
        except Exception:
            LOG.exception("Delete Volume Quotas exception for 'project %s'.",
                          self.project_id)

    def dry_run(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        quotas = self.client.show_quota_set(
            self.project_id, params={'usage': True})['quota_set']
        self.data['volume_quotas'] = quotas


class NovaQuotaService(BaseService):
    def __init__(self, manager, **kwargs):
        super(NovaQuotaService, self).__init__(kwargs)
        self.client = manager.quotas_client
        self.limits_client = manager.limits_client

    def delete(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        client = self.client
        try:
            LOG.debug("Deleting Nova Quotas for project with id %s",
                      self.project_id)
            client.delete_quota_set(self.project_id)
        except Exception:
            LOG.exception("Delete Nova Quotas exception for 'project %s'.",
                          self.project_id)

    def dry_run(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        client = self.limits_client
        quotas = client.show_limits()['limits']
        self.data['compute_quotas'] = quotas['absolute']


class NetworkQuotaService(BaseService):
    def __init__(self, manager, **kwargs):
        super(NetworkQuotaService, self).__init__(kwargs)
        self.client = manager.network_quotas_client

    def delete(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        client = self.client
        try:
            LOG.debug("Deleting Network Quotas for project with id %s",
                      self.project_id)
            client.reset_quotas(self.project_id)
        except Exception:
            LOG.exception("Delete Network Quotas exception for 'project %s'.",
                          self.project_id)

    def dry_run(self):
        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore do nothing
            return
        resp = [quota for quota in self.client.list_quotas()['quotas']
                if quota['project_id'] == self.project_id]
        self.data['network_quotas'] = resp


# Begin network service classes
class BaseNetworkService(BaseService):
    def __init__(self, manager, **kwargs):
        super(BaseNetworkService, self).__init__(kwargs)
        self.networks_client = manager.networks_client
        self.subnets_client = manager.subnets_client
        self.ports_client = manager.ports_client
        self.floating_ips_client = manager.floating_ips_client
        self.metering_labels_client = manager.metering_labels_client
        self.metering_label_rules_client = manager.metering_label_rules_client
        self.security_groups_client = manager.security_groups_client
        self.routers_client = manager.routers_client
        self.subnetpools_client = manager.subnetpools_client

    def _filter_by_conf_networks(self, item_list):
        if not item_list or not all(('network_id' in i for i in item_list)):
            return item_list

        return [item for item in item_list if item['network_id']
                not in CONF_NETWORKS]


class NetworkService(BaseNetworkService):

    def list(self):
        client = self.networks_client
        networks = client.list_networks(**self.tenant_filter)
        networks = networks['networks']

        if self.prefix:
            networks = self._filter_by_prefix(networks)
        elif self.is_resource_list:
            networks = self._filter_by_resource_list(networks, 'networks')
        else:
            if not self.is_save_state:
                # recreate list removing saved networks
                networks = self._filter_out_ids_from_saved(
                    networks, 'networks')
        # filter out networks declared in tempest.conf
        if self.is_preserve:
            networks = [network for network in networks
                        if network['id'] not in CONF_NETWORKS]
        LOG.debug("List count, %s Networks", len(networks))
        return networks

    def delete(self):
        client = self.networks_client
        networks = self.list()
        for n in networks:
            try:
                LOG.debug("Deleting Network with id %s", n['id'])
                client.delete_network(n['id'])
            except Exception:
                LOG.exception("Delete Network %s exception.", n['id'])

    def dry_run(self):
        networks = self.list()
        self.data['networks'] = networks

    def save_state(self):
        networks = self.list()
        self.data['networks'] = {}
        for network in networks:
            self.data['networks'][network['id']] = network


class NetworkFloatingIpService(BaseNetworkService):

    def list(self):
        client = self.floating_ips_client
        flips = client.list_floatingips(**self.tenant_filter)
        flips = flips['floatingips']

        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore return empty list
            return []
        elif self.is_resource_list:
            flips = self._filter_by_resource_list(flips, 'floatingips')
        elif not self.is_save_state:
            # recreate list removing saved flips
            flips = self._filter_out_ids_from_saved(flips, 'floatingips')
        LOG.debug("List count, %s Network Floating IPs", len(flips))
        return flips

    def delete(self):
        client = self.floating_ips_client
        flips = self.list()
        for flip in flips:
            try:
                LOG.debug("Deleting Network Floating IP with id %s",
                          flip['id'])
                client.delete_floatingip(flip['id'])
            except Exception:
                LOG.exception("Delete Network Floating IP %s exception.",
                              flip['id'])

    def dry_run(self):
        flips = self.list()
        self.data['floatingips'] = flips

    def save_state(self):
        flips = self.list()
        self.data['floatingips'] = {}
        for flip in flips:
            self.data['floatingips'][flip['id']] = flip


class NetworkRouterService(BaseNetworkService):

    def list(self):
        client = self.routers_client
        routers = client.list_routers(**self.tenant_filter)
        routers = routers['routers']

        if self.prefix:
            routers = self._filter_by_prefix(routers)
        elif self.is_resource_list:
            routers = self._filter_by_resource_list(routers, 'routers')
        else:
            if not self.is_save_state:
                # recreate list removing saved routers
                routers = self._filter_out_ids_from_saved(routers, 'routers')
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
            rid = router['id']
            ports = [port for port
                     in ports_client.list_ports(device_id=rid)['ports']
                     if net_info.is_router_interface_port(port)]
            for port in ports:
                try:
                    LOG.debug("Deleting port with id %s of router with id %s",
                              port['id'], rid)
                    client.remove_router_interface(rid, port_id=port['id'])
                except Exception:
                    LOG.exception("Delete Router Interface exception for "
                                  "'port %s' of 'router %s'.", port['id'], rid)
            try:
                LOG.debug("Deleting Router with id %s", rid)
                client.delete_router(rid)
            except Exception:
                LOG.exception("Delete Router %s exception.", rid)

    def dry_run(self):
        routers = self.list()
        self.data['routers'] = routers

    def save_state(self):
        routers = self.list()
        self.data['routers'] = {}
        for router in routers:
            self.data['routers'][router['id']] = router['name']


class NetworkMeteringLabelRuleService(NetworkService):

    def list(self):
        client = self.metering_label_rules_client
        rules = client.list_metering_label_rules()
        rules = rules['metering_label_rules']
        rules = self._filter_by_tenant_id(rules)

        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore return empty list
            return []
        elif self.is_resource_list:
            rules = self._filter_by_resource_list(
                rules, 'metering_label_rules')
        elif not self.is_save_state:
            rules = self._filter_out_ids_from_saved(
                rules, 'metering_label_rules')
            # recreate list removing saved rules
        LOG.debug("List count, %s Metering Label Rules", len(rules))
        return rules

    def delete(self):
        client = self.metering_label_rules_client
        rules = self.list()
        for rule in rules:
            try:
                LOG.debug("Deleting Metering Label Rule with id %s",
                          rule['id'])
                client.delete_metering_label_rule(rule['id'])
            except Exception:
                LOG.exception("Delete Metering Label Rule %s exception.",
                              rule['id'])

    def dry_run(self):
        rules = self.list()
        self.data['metering_label_rules'] = rules

    def save_state(self):
        rules = self.list()
        self.data['metering_label_rules'] = {}
        for rule in rules:
            self.data['metering_label_rules'][rule['id']] = rule


class NetworkMeteringLabelService(BaseNetworkService):

    def list(self):
        client = self.metering_labels_client
        labels = client.list_metering_labels()
        labels = labels['metering_labels']
        labels = self._filter_by_tenant_id(labels)

        if self.prefix:
            labels = self._filter_by_prefix(labels)
        elif self.is_resource_list:
            labels = self._filter_by_resource_list(
                labels, 'metering_labels')
        elif not self.is_save_state:
            # recreate list removing saved labels
            labels = self._filter_out_ids_from_saved(
                labels, 'metering_labels')
        LOG.debug("List count, %s Metering Labels", len(labels))
        return labels

    def delete(self):
        client = self.metering_labels_client
        labels = self.list()
        for label in labels:
            try:
                LOG.debug("Deleting Metering Label with id %s", label['id'])
                client.delete_metering_label(label['id'])
            except Exception:
                LOG.exception("Delete Metering Label %s exception.",
                              label['id'])

    def dry_run(self):
        labels = self.list()
        self.data['metering_labels'] = labels

    def save_state(self):
        labels = self.list()
        self.data['metering_labels'] = {}
        for label in labels:
            self.data['metering_labels'][label['id']] = label['name']


class NetworkPortService(BaseNetworkService):

    def list(self):
        client = self.ports_client
        ports = [port for port in
                 client.list_ports(**self.tenant_filter)['ports']
                 if port["device_owner"] == "" or
                 port["device_owner"].startswith("compute:")]

        if self.prefix:
            ports = self._filter_by_prefix(ports)
        elif self.is_resource_list:
            ports = self._filter_by_resource_list(ports, 'ports')
        else:
            if not self.is_save_state:
                # recreate list removing saved ports
                ports = self._filter_out_ids_from_saved(ports, 'ports')
        if self.is_preserve:
            ports = self._filter_by_conf_networks(ports)
        LOG.debug("List count, %s Ports", len(ports))
        return ports

    def delete(self):
        client = self.ports_client
        ports = self.list()
        for port in ports:
            try:
                LOG.debug("Deleting port with id %s", port['id'])
                client.delete_port(port['id'])
            except Exception:
                LOG.exception("Delete Port %s exception.", port['id'])

    def dry_run(self):
        ports = self.list()
        self.data['ports'] = ports

    def save_state(self):
        ports = self.list()
        self.data['ports'] = {}
        for port in ports:
            self.data['ports'][port['id']] = port['name']


class NetworkSecGroupService(BaseNetworkService):
    def list(self):
        client = self.security_groups_client
        filter = self.tenant_filter
        # cannot delete default sec group so never show it.
        secgroups = [secgroup for secgroup in
                     client.list_security_groups(**filter)['security_groups']
                     if secgroup['name'] != 'default']

        if self.prefix:
            secgroups = self._filter_by_prefix(secgroups)
        elif self.is_resource_list:
            secgroups = self._filter_by_resource_list(
                secgroups, 'security_groups')
        else:
            if not self.is_save_state:
                # recreate list removing saved security_groups
                secgroups = self._filter_out_ids_from_saved(
                    secgroups, 'security_groups')
        if self.is_preserve:
            secgroups = [
                secgroup for secgroup in secgroups
                if secgroup['security_group_rules'][0]['project_id']
                not in CONF_PROJECTS]
        LOG.debug("List count, %s security_groups", len(secgroups))
        return secgroups

    def delete(self):
        client = self.security_groups_client
        secgroups = self.list()
        for secgroup in secgroups:
            try:
                LOG.debug("Deleting security_group with id %s", secgroup['id'])
                client.delete_security_group(secgroup['id'])
            except Exception:
                LOG.exception("Delete security_group %s exception.",
                              secgroup['id'])

    def dry_run(self):
        secgroups = self.list()
        self.data['security_groups'] = secgroups

    def save_state(self):
        secgroups = self.list()
        self.data['security_groups'] = {}
        for secgroup in secgroups:
            self.data['security_groups'][secgroup['id']] = secgroup['name']


class NetworkSubnetService(BaseNetworkService):

    def list(self):
        client = self.subnets_client
        subnets = client.list_subnets(**self.tenant_filter)
        subnets = subnets['subnets']

        if self.prefix:
            subnets = self._filter_by_prefix(subnets)
        elif self.is_resource_list:
            subnets = self._filter_by_resource_list(subnets, 'subnets')
        else:
            if not self.is_save_state:
                # recreate list removing saved subnets
                subnets = self._filter_out_ids_from_saved(subnets, 'subnets')
        if self.is_preserve:
            subnets = self._filter_by_conf_networks(subnets)
        LOG.debug("List count, %s Subnets", len(subnets))
        return subnets

    def delete(self):
        client = self.subnets_client
        subnets = self.list()
        for subnet in subnets:
            try:
                LOG.debug("Deleting subnet with id %s", subnet['id'])
                client.delete_subnet(subnet['id'])
            except Exception:
                LOG.exception("Delete Subnet %s exception.", subnet['id'])

    def dry_run(self):
        subnets = self.list()
        self.data['subnets'] = subnets

    def save_state(self):
        subnets = self.list()
        self.data['subnets'] = {}
        for subnet in subnets:
            self.data['subnets'][subnet['id']] = subnet['name']


class NetworkSubnetPoolsService(BaseNetworkService):

    def list(self):
        client = self.subnetpools_client
        pools = client.list_subnetpools(**self.tenant_filter)['subnetpools']

        if self.prefix:
            pools = self._filter_by_prefix(pools)
        elif self.is_resource_list:
            pools = self._filter_by_resource_list(pools, 'subnetpools')
        else:
            if not self.is_save_state:
                # recreate list removing saved subnet pools
                pools = self._filter_out_ids_from_saved(pools, 'subnetpools')
        if self.is_preserve:
            pools = [pool for pool in pools if pool['project_id']
                     not in CONF_PROJECTS]
        LOG.debug("List count, %s Subnet Pools", len(pools))
        return pools

    def delete(self):
        client = self.subnetpools_client
        pools = self.list()
        for pool in pools:
            try:
                LOG.debug("Deleting Subnet Pool with id %s", pool['id'])
                client.delete_subnetpool(pool['id'])
            except Exception:
                LOG.exception("Delete Subnet Pool %s exception.", pool['id'])

    def dry_run(self):
        pools = self.list()
        self.data['subnetpools'] = pools

    def save_state(self):
        pools = self.list()
        self.data['subnetpools'] = {}
        for pool in pools:
            self.data['subnetpools'][pool['id']] = pool['name']


# begin global services
class RegionService(BaseService):

    def __init__(self, manager, **kwargs):
        super(RegionService, self).__init__(kwargs)
        self.client = manager.regions_client

    def list(self):
        client = self.client
        regions = client.list_regions()

        if self.prefix:
            # this means we're cleaning resources based on a certain prefix,
            # this resource doesn't have a name, therefore return empty list
            return []
        elif self.is_resource_list:
            regions = self._filter_by_resource_list(
                regions['regions'], 'regions')
            return regions
        elif not self.is_save_state:
            regions = self._filter_out_ids_from_saved(
                regions['regions'], 'regions')
            LOG.debug("List count, %s Regions", len(regions))
            return regions
        else:
            LOG.debug("List count, %s Regions", len(regions['regions']))
            return regions['regions']

    def delete(self):
        client = self.client
        regions = self.list()
        for region in regions:
            try:
                LOG.debug("Deleting region with id %s", region['id'])
                client.delete_region(region['id'])
            except Exception:
                LOG.exception("Delete Region %s exception.", region['id'])

    def dry_run(self):
        regions = self.list()
        self.data['regions'] = {}
        for region in regions:
            self.data['regions'][region['id']] = region

    def save_state(self):
        regions = self.list()
        self.data['regions'] = {}
        for region in regions:
            self.data['regions'][region['id']] = region


class FlavorService(BaseService):
    def __init__(self, manager, **kwargs):
        super(FlavorService, self).__init__(kwargs)
        self.client = manager.flavors_client

    def list(self):
        client = self.client
        flavors = client.list_flavors({"is_public": None})['flavors']

        if self.prefix:
            flavors = self._filter_by_prefix(flavors)
        elif self.is_resource_list:
            flavors = self._filter_by_resource_list(flavors, 'flavors')
        else:
            if not self.is_save_state:
                # recreate list removing saved flavors
                flavors = self._filter_out_ids_from_saved(flavors, 'flavors')
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
                LOG.debug("Deleting flavor with id %s", flavor['id'])
                client.delete_flavor(flavor['id'])
            except Exception:
                LOG.exception("Delete Flavor %s exception.", flavor['id'])

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
        self.client = manager.image_client_v2

    def list(self):
        client = self.client
        response = client.list_images()
        images = []
        images.extend(response['images'])
        while 'next' in response:
            parsed = urllib.urlparse(response['next'])
            marker = urllib.parse_qs(parsed.query)['marker'][0]
            response = client.list_images(params={"marker": marker})
            images.extend(response['images'])

        if self.prefix:
            images = self._filter_by_prefix(images)
        elif self.is_resource_list:
            images = self._filter_by_resource_list(images, 'images')
        else:
            if not self.is_save_state:
                images = self._filter_out_ids_from_saved(images, 'images')
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
                LOG.debug("Deleting image with id %s", image['id'])
                client.delete_image(image['id'])
            except Exception:
                LOG.exception("Delete Image %s exception.", image['id'])

    def dry_run(self):
        images = self.list()
        self.data['images'] = images

    def save_state(self):
        self.data['images'] = {}
        images = self.list()
        for image in images:
            self.data['images'][image['id']] = image['name']


class UserService(BaseService):

    def __init__(self, manager, **kwargs):
        super(UserService, self).__init__(kwargs)
        self.client = manager.users_v3_client

    def list(self):
        users = self.client.list_users()['users']
        if self.prefix:
            users = self._filter_by_prefix(users)
        elif self.is_resource_list:
            users = self._filter_by_resource_list(users, 'users')
        else:
            if not self.is_save_state:
                users = self._filter_out_ids_from_saved(users, 'users')
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
                LOG.debug("Deleting user with id %s", user['id'])
                self.client.delete_user(user['id'])
            except Exception:
                LOG.exception("Delete User %s exception.", user['id'])

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
        self.client = manager.roles_v3_client

    def list(self):
        try:
            roles = self.client.list_roles()['roles']

            if self.prefix:
                roles = self._filter_by_prefix(roles)
            elif self.is_resource_list:
                roles = self._filter_by_resource_list(roles, 'roles')
            elif not self.is_save_state:
                # reconcile roles with saved state and never list admin role
                roles = self._filter_out_ids_from_saved(roles, 'roles')
                roles = [role for role in roles
                         if role['name'] != CONF.identity.admin_role]
            LOG.debug("List count, %s Roles after reconcile", len(roles))
            return roles
        except Exception:
            LOG.exception("Cannot retrieve Roles.")
            return []

    def delete(self):
        roles = self.list()
        for role in roles:
            try:
                LOG.debug("Deleting role with id %s", role['id'])
                self.client.delete_role(role['id'])
            except Exception:
                LOG.exception("Delete Role %s exception.", role['id'])

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

        if self.prefix:
            projects = self._filter_by_prefix(projects)
        elif self.is_resource_list:
            projects = self._filter_by_resource_list(projects, 'projects')
        else:
            if not self.is_save_state:
                projects = self._filter_out_ids_from_saved(
                    projects, 'projects')
                projects = [project for project in projects
                            if project['name'] != CONF.auth.admin_project_name]
        if self.is_preserve:
            projects = [project for project in projects
                        if project['name'] not in CONF_PROJECTS]
        LOG.debug("List count, %s Projects after reconcile", len(projects))
        return projects

    def delete(self):
        projects = self.list()
        for project in projects:
            try:
                LOG.debug("Deleting project with id %s", project['id'])
                self.client.delete_project(project['id'])
            except Exception:
                LOG.exception("Delete project %s exception.", project['id'])

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

        if self.prefix:
            domains = self._filter_by_prefix(domains)
        elif self.is_resource_list:
            domains = self._filter_by_resource_list(domains, 'domains')
        elif not self.is_save_state:
            domains = self._filter_out_ids_from_saved(domains, 'domains')
        LOG.debug("List count, %s Domains after reconcile", len(domains))
        return domains

    def delete(self):
        client = self.client
        domains = self.list()
        for domain in domains:
            try:
                LOG.debug("Deleting domain with id %s", domain['id'])
                client.update_domain(domain['id'], enabled=False)
                client.delete_domain(domain['id'])
            except Exception:
                LOG.exception("Delete Domain %s exception.", domain['id'])

    def dry_run(self):
        domains = self.list()
        self.data['domains'] = domains

    def save_state(self):
        domains = self.list()
        self.data['domains'] = {}
        for domain in domains:
            self.data['domains'][domain['id']] = domain['name']


def get_project_associated_cleanup_services():
    """Returns list of project service classes.

    The list contains services whose resources need to be deleted prior,
    the project they are associated with, deletion. The resources cannot be
    most likely deleted after the project is deleted first.
    """
    project_associated_services = []
    # TODO(gmann): Tempest should provide some plugin hook for cleanup
    # script extension to plugin tests also.
    if IS_NOVA:
        project_associated_services.append(NovaQuotaService)
    if IS_CINDER:
        project_associated_services.append(VolumeQuotaService)
    if IS_NEUTRON:
        project_associated_services.append(NetworkQuotaService)
    return project_associated_services


def get_resource_cleanup_services():
    """Returns list of project related classes.

    The list contains services whose resources are associated with a project,
    however, their deletion is possible also after the project is deleted
    first.
    """
    resource_cleanup_services = []
    # TODO(gmann): Tempest should provide some plugin hook for cleanup
    # script extension to plugin tests also.
    if IS_NOVA:
        resource_cleanup_services.append(ServerService)
        resource_cleanup_services.append(KeyPairService)
        resource_cleanup_services.append(ServerGroupService)
    if IS_NEUTRON:
        resource_cleanup_services.append(NetworkFloatingIpService)
        if utils.is_extension_enabled('metering', 'network'):
            resource_cleanup_services.append(NetworkMeteringLabelRuleService)
            resource_cleanup_services.append(NetworkMeteringLabelService)
        resource_cleanup_services.append(NetworkRouterService)
        resource_cleanup_services.append(NetworkPortService)
        resource_cleanup_services.append(NetworkSubnetService)
        resource_cleanup_services.append(NetworkService)
        resource_cleanup_services.append(NetworkSecGroupService)
        resource_cleanup_services.append(NetworkSubnetPoolsService)
    if IS_CINDER:
        resource_cleanup_services.append(SnapshotService)
        resource_cleanup_services.append(VolumeService)
    return resource_cleanup_services


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
    global_services.append(RegionService)
    return global_services
