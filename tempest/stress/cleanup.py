#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Quanta Research Cambridge, Inc.
#
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

from tempest import clients
from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def cleanup():
    admin_manager = clients.AdminManager()

    _, body = admin_manager.servers_client.list_servers({"all_tenants": True})
    LOG.info("Cleanup::remove %s servers" % len(body['servers']))
    for s in body['servers']:
        try:
            admin_manager.servers_client.delete_server(s['id'])
        except Exception:
            pass

    for s in body['servers']:
        try:
            admin_manager.servers_client.wait_for_server_termination(s['id'])
        except Exception:
            pass

    _, keypairs = admin_manager.keypairs_client.list_keypairs()
    LOG.info("Cleanup::remove %s keypairs" % len(keypairs))
    for k in keypairs:
        try:
            admin_manager.keypairs_client.delete_keypair(k['name'])
        except Exception:
            pass

    _, floating_ips = admin_manager.floating_ips_client.list_floating_ips()
    LOG.info("Cleanup::remove %s floating ips" % len(floating_ips))
    for f in floating_ips:
        try:
            admin_manager.floating_ips_client.delete_floating_ip(f['id'])
        except Exception:
            pass

    _, users = admin_manager.identity_client.get_users()
    LOG.info("Cleanup::remove %s users" % len(users))
    for user in users:
        if user['name'].startswith("stress_user"):
            admin_manager.identity_client.delete_user(user['id'])

    _, tenants = admin_manager.identity_client.list_tenants()
    LOG.info("Cleanup::remove %s tenants" % len(tenants))
    for tenant in tenants:
        if tenant['name'].startswith("stress_tenant"):
            admin_manager.identity_client.delete_tenant(tenant['id'])

    # We have to delete snapshots first or
    # volume deletion may block

    _, snaps = admin_manager.snapshots_client.\
        list_snapshots({"all_tenants": True})
    LOG.info("Cleanup::remove %s snapshots" % len(snaps))
    for v in snaps:
        try:
            admin_manager.snapshots_client.\
                wait_for_snapshot_status(v['id'], 'available')
            admin_manager.snapshots_client.delete_snapshot(v['id'])
        except Exception:
            pass

    for v in snaps:
        try:
            admin_manager.snapshots_client.wait_for_resource_deletion(v['id'])
        except Exception:
            pass

    _, vols = admin_manager.volumes_client.list_volumes({"all_tenants": True})
    LOG.info("Cleanup::remove %s volumes" % len(vols))
    for v in vols:
        try:
            admin_manager.volumes_client.\
                wait_for_volume_status(v['id'], 'available')
            admin_manager.volumes_client.delete_volume(v['id'])
        except Exception:
            pass

    for v in vols:
        try:
            admin_manager.volumes_client.wait_for_resource_deletion(v['id'])
        except Exception:
            pass
