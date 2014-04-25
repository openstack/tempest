#!/usr/bin/env python

# Copyright 2013 IBM Corp.
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

import json
import sys
import urlparse

import httplib2

from tempest import clients
from tempest import config


CONF = config.CONF
RAW_HTTP = httplib2.Http()


def verify_glance_api_versions(os):
    # Check glance api versions
    __, versions = os.image_client.get_versions()
    if CONF.image_feature_enabled.api_v1 != ('v1.1' in versions or 'v1.0' in
                                             versions):
        print('Config option image api_v1 should be change to: %s' % (
            not CONF.image_feature_enabled.api_v1))
    if CONF.image_feature_enabled.api_v2 != ('v2.0' in versions):
        print('Config option image api_v2 should be change to: %s' % (
            not CONF.image_feature_enabled.api_v2))


def _get_api_versions(os, service):
    client_dict = {
        'nova': os.servers_client,
        'keystone': os.identity_client,
    }
    client_dict[service].skip_path()
    endpoint_parts = urlparse.urlparse(client_dict[service].base_url)
    endpoint = endpoint_parts.scheme + '://' + endpoint_parts.netloc
    __, body = RAW_HTTP.request(endpoint, 'GET')
    client_dict[service].reset_path()
    body = json.loads(body)
    if service == 'keystone':
        versions = map(lambda x: x['id'], body['versions']['values'])
    else:
        versions = map(lambda x: x['id'], body['versions'])
    return versions


def verify_keystone_api_versions(os):
    # Check keystone api versions
    versions = _get_api_versions(os, 'keystone')
    if CONF.identity_feature_enabled.api_v2 != ('v2.0' in versions):
        print('Config option identity api_v2 should be change to %s' % (
            not CONF.identity_feature_enabled.api_v2))
    if CONF.identity_feature_enabled.api_v3 != ('v3.0' in versions):
        print('Config option identity api_v3 should be change to %s' % (
            not CONF.identity_feature_enabled.api_v3))


def verify_nova_api_versions(os):
    versions = _get_api_versions(os, 'nova')
    if CONF.compute_feature_enabled.api_v3 != ('v3.0' in versions):
        print('Config option compute api_v3 should be change to: %s' % (
              not CONF.compute_feature_enabled.api_v3))


def get_extension_client(os, service):
    extensions_client = {
        'nova': os.extensions_client,
        'nova_v3': os.extensions_v3_client,
        'cinder': os.volumes_extension_client,
        'neutron': os.network_client,
        'swift': os.account_client,
    }
    if service not in extensions_client:
        print('No tempest extensions client for %s' % service)
        exit(1)
    return extensions_client[service]


def get_enabled_extensions(service):
    extensions_options = {
        'nova': CONF.compute_feature_enabled.api_extensions,
        'nova_v3': CONF.compute_feature_enabled.api_v3_extensions,
        'cinder': CONF.volume_feature_enabled.api_extensions,
        'neutron': CONF.network_feature_enabled.api_extensions,
        'swift': CONF.object_storage_feature_enabled.discoverable_apis,
    }
    if service not in extensions_options:
        print('No supported extensions list option for %s' % service)
        exit(1)
    return extensions_options[service]


def verify_extensions(os, service, results):
    extensions_client = get_extension_client(os, service)
    __, resp = extensions_client.list_extensions()
    if isinstance(resp, dict):
        # Neutron's extension 'name' field has is not a single word (it has
        # spaces in the string) Since that can't be used for list option the
        # api_extension option in the network-feature-enabled group uses alias
        # instead of name.
        if service == 'neutron':
            extensions = map(lambda x: x['alias'], resp['extensions'])
        elif service == 'swift':
            # Remove Swift general information from extensions list
            resp.pop('swift')
            extensions = resp.keys()
        else:
            extensions = map(lambda x: x['name'], resp['extensions'])

    else:
        extensions = map(lambda x: x['name'], resp)
    if not results.get(service):
        results[service] = {}
    extensions_opt = get_enabled_extensions(service)
    if extensions_opt[0] == 'all':
        results[service]['extensions'] = 'all'
        return results
    # Verify that all configured extensions are actually enabled
    for extension in extensions_opt:
        results[service][extension] = extension in extensions
    # Verify that there aren't additional extensions enabled that aren't
    # specified in the config list
    for extension in extensions:
        if extension not in extensions_opt:
            results[service][extension] = False
    return results


def display_results(results):
    for service in results:
        # If all extensions are specified as being enabled there is no way to
        # verify this so we just assume this to be true
        if results[service].get('extensions'):
            continue
        extension_list = get_enabled_extensions(service)
        for extension in results[service]:
            if not results[service][extension]:
                if extension in extension_list:
                    print("%s extension: %s should not be included in the list"
                          " of enabled extensions" % (service, extension))
                else:
                    print("%s extension: %s should be included in the list of "
                          "enabled extensions" % (service, extension))


def check_service_availability(os):
    services = []
    avail_services = []
    codename_match = {
        'volume': 'cinder',
        'network': 'neutron',
        'image': 'glance',
        'object_storage': 'swift',
        'compute': 'nova',
        'orchestration': 'heat',
        'metering': 'ceilometer',
        'telemetry': 'ceilometer',
        'data_processing': 'sahara',
        'baremetal': 'ironic',
        'identity': 'keystone',
        'queuing': 'marconi',
        'database': 'trove'
    }
    # Get catalog list for endpoints to use for validation
    __, endpoints = os.endpoints_client.list_endpoints()
    for endpoint in endpoints:
        __, service = os.service_client.get_service(endpoint['service_id'])
        services.append(service['type'])
    # Pull all catalog types from config file and compare against endpoint list
    for cfgname in dir(CONF._config):
        cfg = getattr(CONF, cfgname)
        catalog_type = getattr(cfg, 'catalog_type', None)
        if not catalog_type:
            continue
        else:
            if cfgname == 'identity':
                # Keystone is a required service for tempest
                continue
            if catalog_type not in services:
                if getattr(CONF.service_available, codename_match[cfgname]):
                    print('Endpoint type %s not found either disable service '
                          '%s or fix the catalog_type in the config file' % (
                          catalog_type, codename_match[cfgname]))
            else:
                if not getattr(CONF.service_available,
                               codename_match[cfgname]):
                    print('Endpoint type %s is available, service %s should be'
                          ' set as available in the config file.' % (
                          catalog_type, codename_match[cfgname]))
                else:
                    avail_services.append(codename_match[cfgname])
    return avail_services


def main(argv):
    print('Running config verification...')
    os = clients.ComputeAdminManager(interface='json')
    services = check_service_availability(os)
    results = {}
    for service in ['nova', 'nova_v3', 'cinder', 'neutron', 'swift']:
        if service == 'nova_v3' and 'nova' not in services:
            continue
        elif service not in services:
            continue
        results = verify_extensions(os, service, results)
    verify_keystone_api_versions(os)
    verify_glance_api_versions(os)
    verify_nova_api_versions(os)
    display_results(results)


if __name__ == "__main__":
    main(sys.argv)
