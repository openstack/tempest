#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Javelin makes resources that should survive an upgrade.

Javelin is a tool for creating, verifying, and deleting a small set of
resources in a declarative way.

"""

import logging
import os
import sys
import unittest
import yaml

import argparse

import tempest.auth
from tempest import exceptions
from tempest.services.compute.json import flavors_client
from tempest.services.compute.json import servers_client
from tempest.services.identity.json import identity_client
from tempest.services.image.v2.json import image_client
from tempest.services.object_storage import container_client
from tempest.services.object_storage import object_client

OPTS = {}
USERS = {}
RES = {}

LOG = None


class OSClient(object):
    _creds = None
    identity = None
    servers = None

    def __init__(self, user, pw, tenant):
        _creds = tempest.auth.KeystoneV2Credentials(
            username=user,
            password=pw,
            tenant_name=tenant)
        _auth = tempest.auth.KeystoneV2AuthProvider(_creds)
        self.identity = identity_client.IdentityClientJSON(_auth)
        self.servers = servers_client.ServersClientJSON(_auth)
        self.objects = object_client.ObjectClient(_auth)
        self.containers = container_client.ContainerClient(_auth)
        self.images = image_client.ImageClientV2JSON(_auth)
        self.flavors = flavors_client.FlavorsClientJSON(_auth)


def load_resources(fname):
    """Load the expected resources from a yaml flie."""
    return yaml.load(open(fname, 'r'))


def keystone_admin():
    return OSClient(OPTS.os_username, OPTS.os_password, OPTS.os_tenant_name)


def client_for_user(name):
    LOG.debug("Entering client_for_user")
    if name in USERS:
        user = USERS[name]
        LOG.debug("Created client for user %s" % user)
        return OSClient(user['name'], user['pass'], user['tenant'])
    else:
        LOG.error("%s not found in USERS: %s" % (name, USERS))

###################
#
# TENANTS
#
###################


def create_tenants(tenants):
    """Create tenants from resource definition.

    Don't create the tenants if they already exist.
    """
    admin = keystone_admin()
    _, body = admin.identity.list_tenants()
    existing = [x['name'] for x in body]
    for tenant in tenants:
        if tenant not in existing:
            admin.identity.create_tenant(tenant)
        else:
            LOG.warn("Tenant '%s' already exists in this environment" % tenant)

##############
#
# USERS
#
##############


def _users_for_tenant(users, tenant):
    u_for_t = []
    for user in users:
        for n in user:
            if user[n]['tenant'] == tenant:
                u_for_t.append(user[n])
    return u_for_t


def _tenants_from_users(users):
    tenants = set()
    for user in users:
        for n in user:
            tenants.add(user[n]['tenant'])
    return tenants


def _assign_swift_role(user):
    admin = keystone_admin()
    resp, roles = admin.identity.list_roles()
    role = next(r for r in roles if r['name'] == 'Member')
    LOG.debug(USERS[user])
    try:
        admin.identity.assign_user_role(
            USERS[user]['tenant_id'],
            USERS[user]['id'],
            role['id'])
    except exceptions.Conflict:
        # don't care if it's already assigned
        pass


def create_users(users):
    """Create tenants from resource definition.

    Don't create the tenants if they already exist.
    """
    global USERS
    LOG.info("Creating users")
    admin = keystone_admin()
    for u in users:
        try:
            tenant = admin.identity.get_tenant_by_name(u['tenant'])
        except exceptions.NotFound:
            LOG.error("Tenant: %s - not found" % u['tenant'])
            continue
        try:
            admin.identity.get_user_by_username(tenant['id'], u['name'])
            LOG.warn("User '%s' already exists in this environment"
                     % u['name'])
        except exceptions.NotFound:
            admin.identity.create_user(
                u['name'], u['pass'], tenant['id'],
                "%s@%s" % (u['name'], tenant['id']),
                enabled=True)


def collect_users(users):
    global USERS
    LOG.info("Creating users")
    admin = keystone_admin()
    for u in users:
        tenant = admin.identity.get_tenant_by_name(u['tenant'])
        u['tenant_id'] = tenant['id']
        USERS[u['name']] = u
        body = admin.identity.get_user_by_username(tenant['id'], u['name'])
        USERS[u['name']]['id'] = body['id']


class JavelinCheck(unittest.TestCase):
    def __init__(self, users, resources):
        super(JavelinCheck, self).__init__()
        self.users = users
        self.res = resources

    def runTest(self, *args):
        pass

    def check(self):
        self.check_users()
        self.check_objects()
        self.check_servers()

    def check_users(self):
        """Check that the users we expect to exist, do.

        We don't use the resource list for this because we need to validate
        that things like tenantId didn't drift across versions.
        """
        for name, user in self.users.iteritems():
            client = keystone_admin()
            _, found = client.identity.get_user(user['id'])
            self.assertEqual(found['name'], user['name'])
            self.assertEqual(found['tenantId'], user['tenant_id'])

            # also ensure we can auth with that user, and do something
            # on the cloud. We don't care about the results except that it
            # remains authorized.
            client = client_for_user(user['name'])
            resp, body = client.servers.list_servers()
            self.assertEqual(resp['status'], '200')

    def check_objects(self):
        """Check that the objects created are still there."""
        for obj in self.res['objects']:
            client = client_for_user(obj['owner'])
            r, contents = client.objects.get_object(
                obj['container'], obj['name'])
            source = _file_contents(obj['file'])
            self.assertEqual(contents, source)

    def check_servers(self):
        """Check that the servers are still up and running."""
        for server in self.res['servers']:
            client = client_for_user(server['owner'])
            found = _get_server_by_name(client, server['name'])
            self.assertIsNotNone(
                found,
                "Couldn't find expected server %s" % server['name'])

            r, found = client.servers.get_server(found['id'])
            # get the ipv4 address
            addr = found['addresses']['private'][0]['addr']
            self.assertEqual(os.system("ping -c 1 " + addr), 0,
                             "Server %s is not pingable at %s" % (
                                 server['name'], addr))


#######################
#
# OBJECTS
#
#######################


def _file_contents(fname):
    with open(fname, 'r') as f:
        return f.read()


def create_objects(objects):
    LOG.info("Creating objects")
    for obj in objects:
        LOG.debug("Object %s" % obj)
        _assign_swift_role(obj['owner'])
        client = client_for_user(obj['owner'])
        client.containers.create_container(obj['container'])
        client.objects.create_object(
            obj['container'], obj['name'],
            _file_contents(obj['file']))

#######################
#
# IMAGES
#
#######################


def create_images(images):
    for image in images:
        client = client_for_user(image['owner'])

        # only upload a new image if the name isn't there
        r, body = client.images.image_list()
        names = [x['name'] for x in body]
        if image['name'] in names:
            continue

        # special handling for 3 part image
        extras = {}
        if image['format'] == 'ami':
            r, aki = client.images.create_image(
                'javelin_' + image['aki'], 'aki', 'aki')
            client.images.store_image(aki.get('id'), open(image['aki'], 'r'))
            extras['kernel_id'] = aki.get('id')

            r, ari = client.images.create_image(
                'javelin_' + image['ari'], 'ari', 'ari')
            client.images.store_image(ari.get('id'), open(image['ari'], 'r'))
            extras['ramdisk_id'] = ari.get('id')

        r, body = client.images.create_image(
            image['name'], image['format'], image['format'], **extras)
        image_id = body.get('id')
        client.images.store_image(image_id, open(image['file'], 'r'))


#######################
#
# SERVERS
#
#######################

def _get_server_by_name(client, name):
    r, body = client.servers.list_servers()
    for server in body['servers']:
        if name == server['name']:
            return server
    return None


def _get_image_by_name(client, name):
    r, body = client.images.image_list()
    for image in body:
        if name == image['name']:
            return image
    return None


def _get_flavor_by_name(client, name):
    r, body = client.flavors.list_flavors()
    for flavor in body:
        if name == flavor['name']:
            return flavor
    return None


def create_servers(servers):
    for server in servers:
        client = client_for_user(server['owner'])

        if _get_server_by_name(client, server['name']):
            continue

        image_id = _get_image_by_name(client, server['image'])['id']
        flavor_id = _get_flavor_by_name(client, server['flavor'])['id']
        client.servers.create_server(server['name'], image_id, flavor_id)


#######################
#
# MAIN LOGIC
#
#######################

def create_resources():
    LOG.info("Creating Resources")
    # first create keystone level resources, and we need to be admin
    # for those.
    create_tenants(RES['tenants'])
    create_users(RES['users'])
    collect_users(RES['users'])

    # next create resources in a well known order
    create_objects(RES['objects'])
    create_images(RES['images'])
    create_servers(RES['servers'])


def get_options():
    global OPTS
    parser = argparse.ArgumentParser(
        description='Create and validate a fixed set of OpenStack resources')
    parser.add_argument('-m', '--mode',
                        metavar='<create|check|destroy>',
                        required=True,
                        help=('One of (create, check, destroy)'))
    parser.add_argument('-r', '--resources',
                        required=True,
                        metavar='resourcefile.yaml',
                        help='Resources definition yaml file')
    # auth bits, letting us also just source the devstack openrc
    parser.add_argument('--os-username',
                        metavar='<auth-user-name>',
                        default=os.environ.get('OS_USERNAME'),
                        help=('Defaults to env[OS_USERNAME].'))
    parser.add_argument('--os-password',
                        metavar='<auth-password>',
                        default=os.environ.get('OS_PASSWORD'),
                        help=('Defaults to env[OS_PASSWORD].'))
    parser.add_argument('--os-tenant-name',
                        metavar='<auth-tenant-name>',
                        default=os.environ.get('OS_TENANT_NAME'),
                        help=('Defaults to env[OS_TENANT_NAME].'))

    OPTS = parser.parse_args()
    if OPTS.mode not in ('create', 'check', 'destroy'):
        print("ERROR: Unknown mode -m %s\n" % OPTS.mode)
        parser.print_help()
        sys.exit(1)


def setup_logging(debug=True):
    global LOG
    LOG = logging.getLogger(__name__)
    if debug:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        fmt='%(asctime)s.%(msecs).03d - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    LOG.addHandler(ch)


def main():
    global RES
    get_options()
    setup_logging()
    RES = load_resources(OPTS.resources)

    if OPTS.mode == 'create':
        create_resources()
    elif OPTS.mode == 'check':
        collect_users(RES['users'])
        checker = JavelinCheck(USERS, RES)
        checker.check()
    elif OPTS.mode == 'destroy':
        LOG.warn("Destroy mode not yet implemented")
    else:
        LOG.error('Unknown mode %s' % OPTS.mode)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
