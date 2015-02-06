# Ensure cirros 0.3.3 is the image in tempest
# Ensure that allow overlapping tenants is set to false?
# tempest.conf is configured properly, and tenants are clean

import glanceclient.v2.client as glclient
import keystoneclient.v2_0.client as ksclient
import os
import pip

from pkg_resources import WorkingSet, DistributionNotFound

try:
    working_set = WorkingSet()
    dep = working_set.require('SimpleConfigParser')
except DistributionNotFound:
    pip.main(['install', 'SimpleConfigParser'])

from simpleconfigparser import simpleconfigparser
from tempest import auth
from tempest import clients
from tempest import config

CONF = config.CONF
image_ref = None
tenant = None


def main():
    credentials = auth.get_default_credentials('identity_admin')
    network_client, image_client, glance_client = set_context(credentials)
    # Start to config
    fix_cirros(glance_client, image_client)
    fix_tempest_conf(network_client)


def set_context(credentials):
    keystone = ksclient.Client(**_get_keystone_credentials(credentials))
    manager = clients.Manager(credentials=credentials)
    network_client = manager.network_client
    image_client = manager.image_client
    glance_endpoint = keystone.service_catalog.url_for(
        service_type='image',
        endpoint_type='internal')
    glance_client =\
        glclient.Client(glance_endpoint,
                        token=keystone.auth_token)
    return network_client, image_client, glance_client


def _get_keystone_credentials(credentials):
    d = {}
    d['username'] = credentials.username
    d['password'] = credentials.password
    d['auth_url'] = CONF.identity.uri
    d['tenant_name'] = credentials.tenant_name
    d['endpoint_type'] = 'public'
    return d


def fix_cirros(glance_client, image_client):
    global image_ref
    images = glance_client.images.list()
    flag = 1
    for img in images:
        if img['checksum'] == '133eae9fb1c98f45894a4e60d8736619' and img[
                'visibility'] == 'public':
            image_ref = img['id']
            flag = 0
            break
    if flag > 0:
        upload_cirros(image_client)


def upload_cirros(image_client):
    # create and image with cirros 0.3.3
    global image_ref
    kwargs = {
        'copy_from': 'http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img',
        'visibility': 'public',
        'is_public': True,
    }
    try:
        resp = image_client.create_image(name='cirros 0.3.3',
                                         container_format='bare',
                                         disk_format='raw',
                                         **kwargs)
    except:
        raise Exception("Cirros image not created")

    image_ref = resp['id']


def fix_tempest_conf(network_client):
    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "/tempest.conf"
    _path = DEFAULT_CONFIG_DIR + DEFAULT_CONFIG_FILE
    if not os.path.isfile(_path):
        raise Exception("No config file in %s", _path)

    try:
        config = simpleconfigparser()
        config.read(_path)
    except Exception as e:
        print(str(e))

    # get neutron suported extensions
    extensions_dict = network_client.list_extensions()
    extensions_unfiltered = [x['alias'] for x in extensions_dict['extensions']]
    # setup network extensions
    extensions = [x for x in extensions_unfiltered
                  if x not in ['lbaas', 'fwaas']]
    to_string = ""
    for ex in extensions[:-1]:
        if ex != "lbaas" or ex != "fwaas":
            to_string = str.format("{0},{1}", ex, to_string)
    to_string = str.format("{0}{1}", to_string, extensions[-1])

    if CONF.network_feature_enabled.api_extensions != to_string:
        # modify tempest.conf file
        config.set('network-feature-enabled',
                   'api_extensions', to_string)

    # set up image_ref
    if image_ref:
        config.set('compute', 'image_ref', image_ref)

    # set up allow_tenant_isolation
    try:
        if not config.get('auth', 'allow_tenant_isolation'):
            config.set('auth', 'allow_tenant_isolation', 'True')
    except:
        if not config.get('compute', 'allow_tenant_isolation'):
            config.set('compute', 'allow_tenant_isolation', 'True')

    # increase ssh timeouts to minimize false gateway failures
    config.set('compute', 'ssh_timeout', '300')
    config.set('compute', 'ssh_channel_timeout', '60')

    with open(_path, 'w') as tempest_conf:
        config.write(tempest_conf)

if __name__ == "__main__":
    main()
