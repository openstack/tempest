#!/usr/bin/env python

# Copyright 2014 Red Hat, Inc.
# All Rights Reserved.
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

import argparse
import glanceclient as glance_client
import keystoneclient.exceptions as keystone_exception
import keystoneclient.v2_0.client as keystone_client
import logging
import neutronclient.v2_0.client as neutron_client
import novaclient.client as nova_client
import sys
import tempfile
import urllib2

LOG = logging.getLogger(__name__)


class AdminClientManager(object):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """
    def __init__(self, conf, has_neutron):
        self.conf = conf
        # identity client
        creds = {'username': conf.get('identity', 'admin_username'),
                 'password': conf.get('identity', 'admin_password'),
                 'tenant_name': conf.get('identity', 'admin_tenant_name'),
                 'auth_url': conf.get('identity', 'uri'),
                 'insecure': conf.get('identity',
                                      'disable_ssl_certificate_validation'
                                      )
             }
        LOG.debug(creds)
        self.identity_client = keystone_client.Client(**creds)

        # compute client
        dscv = conf.get('identity', 'disable_ssl_certificate_validation')
        username = conf.get('identity', 'admin_username')
        password = conf.get('identity', 'admin_password')
        tenantname = conf.get('identity', 'admin_tenant_name')
        auth_url = conf.get('identity', 'uri')
        kwargs = {'insecure': dscv,
                  'no_cache': True}
        self.compute_client = nova_client.Client('2', username, password,
                                                 tenantname, auth_url,
                                                 **kwargs)

        # network client
        if has_neutron:
            self.network_client = neutron_client.Client(username=username,
                                                        password=password,
                                                        tenant_name=tenantname,
                                                        auth_url=auth_url,
                                                        insecure=dscv)
        # image client
        token = self.identity_client.auth_token
        endpoint = self.identity_client.\
        service_catalog.url_for(service_type='image',
                                endpoint_type='publicURL'
                            )
        dscv = self.conf.get('identity',
                             'disable_ssl_certificate_validation')
        creds = {'endpoint': endpoint,
                 'token': token,
                 'insecure': dscv}
        self.image_client = glance_client.Client("1", **creds)

    def create_users_and_tenants(self):
        LOG.debug("Creating users and tenants")
        conf = self.conf
        self.create_user_with_tenant(conf.get('identity', 'username'),
                                     conf.get('identity', 'password'),
                                     conf.get('identity', 'tenant_name'))

        self.create_user_with_tenant(conf.get('identity', 'alt_username'),
                                     conf.get('identity', 'alt_password'),
                                     conf.get('identity', 'alt_tenant_name'))

    def create_user_with_tenant(self, username, password, tenant_name):
        # Try to create the necessary tenant
        tenant_id = None
        try:
            tenant_description = "Tenant for Tempest %s user" % username
            tenant = self.identity_client.tenants.create(tenant_name,
                                                         tenant_description)
            tenant_id = tenant.id
        except keystone_exception.Conflict:
            # if already exist, use existing tenant
            tenant_list = self.identity_client.tenants.list()
            for tenant in tenant_list:
                if tenant.name == tenant_name:
                    tenant_id = tenant.id

        try:
            email = "%s@test.com" % username
            self.identity_client.users.create(name=username,
                                              password=password,
                                              email=email,
                                              tenant_id=tenant_id)
        except keystone_exception.Conflict:
            pass

    def create_flavors(self):
        LOG.debug("Creating flavors")
        flavor_id = None
        flavor_alt_id = None
        max_id = 1
        for flavor in self.compute_client.flavors.list():
            if flavor.name == "m1.nano":
                flavor_id = flavor.id
            if flavor.name == "m1.micro":
                flavor_alt_id = flavor.id
            try:
                max_id = max(max_id, int(flavor.id))
            except ValueError:
                pass
        if not flavor_id:
            flavor = self.compute_client.flavors.create("m1.nano", 64, 1, 0,
                                                        flavorid=max_id + 1)
            flavor_id = flavor.id
        if not flavor_alt_id:
            flavor = self.compute_client.flavors.create("m1.micro", 128, 1, 0,
                                                        flavorid=max_id + 2)
            flavor_alt_id = flavor.id
        if not self.conf.is_modified('compute', 'flavor_ref'):
            self.conf.set('compute', 'flavor_ref', flavor_id)
        if not self.conf.is_modified('compute', 'flavor_ref_alt'):
            self.conf.set('compute', 'flavor_ref_alt', flavor_alt_id)

    def upload_image(self, name, data):
        data.seek(0)
        return self.image_client.images.create(name=name,
                                               disk_format="qcow2",
                                               container_format="bare",
                                               data=data,
                                               is_public="true")

    def create_images(self, path):
        LOG.debug("Creating images")
        name = path[path.rfind('/') + 1:]
        name_alt = name + "_alt"
        image_id = None
        image_alt_id = None
        for image in self.image_client.images.list():
            if image.name == name:
                image_id = image.id
            if image.name == name_alt:
                image_alt_id = image.id
        if not (image_id and image_alt_id):
            if path.startswith("http:") or path.startswith("https:"):
                request = urllib2.urlopen(path)
                with tempfile.NamedTemporaryFile() as data:
                    while True:
                        chunk = request.read(64 * 1024)
                        if not chunk:
                            break
                        data.write(chunk)

                    data.flush()
                    if not image_id:
                        image_id = self.upload_image(name, data).id
                    if not image_alt_id:
                        image_alt_id = self.upload_image(name_alt, data).id
            else:
                with open(path) as data:
                    if not image_id:
                        image_id = self.upload_image(name, data).id
                    if not image_alt_id:
                        image_alt_id = self.upload_image(name_alt, data).id

        self.conf.set('compute', 'image_ref', image_id)
        self.conf.set('compute', 'image_ref_alt', image_alt_id)

    def set_networks(self, has_neutron):
        if has_neutron:
            for router in self.network_client.list_routers()['routers']:
                if "external_gateway_info" in router:
                    net_id = router['external_gateway_info']['network_id']
                    self.conf.set('network', 'public_network_id', net_id)
                    self.conf.set('network', 'public_router_id', router['id'])
            for network in self.compute_client.networks.list():
                if network.id != net_id:
                    label = network.label
                    break
        else:
            label = self.compute_client.networks.list()[0].label
        self.conf.set('compute', 'fixed_network_name', label)


class TempestConf():
    def __init__(self, tempest_conf):
        self.lines = []
        self.sections = {}
        self.modified = {}
        section = None
        index = -1
        for line in open(tempest_conf):
            index += 1
            self.lines.append(line)
            if line.startswith('# '):
                continue
            stripped = line.strip()
            if stripped.startswith('['):
                name = stripped[1:stripped.find(']')]
                section = {}
                self.sections[name] = section
                self.modified[name] = {}
                continue
            if not stripped:
                continue
            if stripped.startswith('#'):
                stripped = stripped[1:]
            equal = stripped.find('=')
            key = stripped[:equal].strip()
            value = stripped[equal + 1:].strip()
            section[key] = (value, index)

    def write(self, conf_file):
        for section in self.modified.values():
            for (key, (value, index)) in section.iteritems():
                if value.strip() != value:
                    value = '"%s"' % value
                self.lines[index] = "%s=%s\n" % (key, value)
        with open(conf_file, "w") as out:
            for line in self.lines:
                out.write(line)

    def get(self, section, key):
        if key in self.modified[section]:
            return self.modified[section][key][0]
        return self.sections[section][key][0]

    def set(self, section, key, value):
        (_, index) = self.sections[section][key]
        self.modified[section][key] = (value, index)

    def is_modified(self, section, key):
        return key in self.modified[section]

    def set_service(self, name, section, services):
        if section not in self.sections:
            return
        catalog_type = self.get(section, 'catalog_type')
        old = self.get('service_available', name)
        new = str(catalog_type in services)
        if old.lower() != new.lower():
            self.set('service_available', name, str(new))

    def get_services(self, is_admin):
        LOG.debug("Getting services")
        if is_admin:
            (username, password, tenant_name) = ('admin_username',
                                                 'admin_password',
                                                 'admin_tenant_name')
        else:
            (username, password, tenant_name) = ('username',
                                                 'password',
                                                 'tenant_name')

        creds = {'username': self.get('identity', username),
                 'password': self.get('identity', password),
                 'tenant_name': self.get('identity', tenant_name),
                 'auth_url': self.get('identity', 'uri'),
                 'insecure': self.get('identity',
                                      'disable_ssl_certificate_validation'
                                      )
                 }
        LOG.debug(creds)
        client = keystone_client.Client(**creds)
        services = client.service_catalog.get_endpoints()
        return services

    def set_service_available(self, services):
        self.set_service('ironic', 'baremetal', services)
        self.set_service('nova', 'compute', services)
        self.set_service('savanna', 'data_processing', services)
        self.set_service('glance', 'image', services)
        self.set_service('neutron', 'network', services)
        self.set_service('swift', 'object-storage', services)
        self.set_service('heat', 'orchestration', services)
        self.set_service('ceilometer', 'telemetry', services)
        self.set_service('cinder', 'volume', services)

    def create_resources(self, image, has_neutron):
        LOG.debug("Creating resources")
        manager = AdminClientManager(self, has_neutron)
        manager.create_users_and_tenants()
        manager.create_flavors()
        manager.create_images(image)
        manager.set_networks(has_neutron)


def configure_tempest(sample=None, out=None, query=False, create=False,
                      overrides=[], image=None, patch=None):
    LOG.debug("Configuring from %s to %s" % (sample, out))
    conf = TempestConf(sample)
    if patch:
        for (section, values) in TempestConf(patch).sections.iteritems():
            for (key, (value, _index)) in values.iteritems():
                conf.set(section, key, value)
    i = 0
    while i < len(overrides):
        keyparts = overrides[i].split('.')
        assert len(keyparts) == 2, keyparts
        conf.set(keyparts[0], keyparts[1], overrides[i + 1])
        i += 2
    services = conf.get_services(create)
    if create:
        if image is None:
            image = "http://download.cirros-cloud.net/0.3.1/" \
                    "cirros-0.3.1-x86_64-disk.img"
        conf.create_resources(image, "network" in services)
    if query:
        conf.set_service_available(services)
    LOG.debug("Writing conf file")
    conf.write(out)

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Generate the tempest.conf file")
    parser.add_argument('--query', action='store_true', default=False,
                        help='query the endpoint for services')
    parser.add_argument('--create', action='store_true', default=False,
                        help='create default tempest resources')
    parser.add_argument('--sample', default="etc/tempest.conf.sample",
                        help='the sample tempest.conf file to read')
    parser.add_argument('--out', default="etc/tempest.conf",
                        help='the tempest.conf file to write')
    parser.add_argument('--patch', default=None,
                        help="""A file in the format of tempest.conf that will
                                override the values in the sample input. The
                                patch file is an alternative to providing
                                key/value pairs. If there are also key/value
                                pairs they will be applied after the patch
                                file""")
    parser.add_argument('overrides', nargs='*', default=[],
                        help="""key value pairs to modify. The key is
                                section.key where section is a section header
                                in the conf file.
                                For example: identity.username myname
                                 identity.password mypass""")
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Send log to stdout')
    parser.add_argument('--image', default=None,
                        help="""an image to be uploaded to glance. The name of
                                the image is the leaf name of the path which
                                can be either a filename or url. Default is
                                http://download.cirros-cloud.net/0.3.1/
                                cirros-0.3.1-x86_64-disk.img """)

    ns = parser.parse_args()

    if ns.debug:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt)
        ch.setFormatter(formatter)
        LOG.setLevel(logging.DEBUG)
        LOG.addHandler(ch)

    configure_tempest(sample=ns.sample, out=ns.out, query=ns.query,
                      create=ns.create, overrides=ns.overrides, image=ns.image,
                      patch=ns.patch)
