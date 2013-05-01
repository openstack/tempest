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


def cleanup():
    admin_manager = clients.AdminManager()

    _, body = admin_manager.servers_client.list_servers({"all_tenants": True})
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
    for k in keypairs:
        try:
            admin_manager.keypairs_client.delete_keypair(k['name'])
        except Exception:
            pass

    _, floating_ips = admin_manager.floating_ips_client.list_floating_ips()
    for f in floating_ips:
        try:
            admin_manager.floating_ips_client.delete_floating_ip(f['id'])
        except Exception:
            pass

    _, users = admin_manager.identity_client.get_users()
    for user in users:
        if user['name'].startswith("stress_user"):
            admin_manager.identity_client.delete_user(user['id'])

    _, tenants = admin_manager.identity_client.list_tenants()
    for tenant in tenants:
        if tenant['name'].startswith("stress_tenant"):
            admin_manager.identity_client.delete_tenant(tenant['id'])
