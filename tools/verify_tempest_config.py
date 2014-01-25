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

import sys

from tempest import clients
from tempest import config


CONF = config.CONF


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


def get_extension_client(os, service):
    extensions_client = {
        'nova': os.extensions_client,
        'nova_v3': os.extensions_v3_client,
        'cinder': os.volumes_extension_client,
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
    }
    if service not in extensions_options:
        print('No supported extensions list option for %s' % service)
        exit(1)
    return extensions_options[service]


def verify_extensions(os, service, results):
    extensions_client = get_extension_client(os, service)
    __, resp = extensions_client.list_extensions()
    if isinstance(resp, dict):
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


def main(argv):
    print('Running config verification...')
    os = clients.ComputeAdminManager(interface='json')
    results = {}
    for service in ['nova', 'nova_v3', 'cinder']:
        results = verify_extensions(os, service, results)
    verify_glance_api_versions(os)
    display_results(results)


if __name__ == "__main__":
    main(sys.argv)
