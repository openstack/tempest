#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

#Dicts matching extension names to config options
NOVA_EXTENSIONS = {
    'disk_config': 'DiskConfig',
    'change_password': 'ServerPassword',
    'flavor_extra': 'FlavorExtraSpecs'
}


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


def verify_extensions(os):
    results = {}
    extensions_client = os.extensions_client
    __, resp = extensions_client.list_extensions()
    resp = resp['extensions']
    extensions = map(lambda x: x['name'], resp)
    results['nova_features'] = {}
    for extension in NOVA_EXTENSIONS.keys():
        if NOVA_EXTENSIONS[extension] in extensions:
            results['nova_features'][extension] = True
        else:
            results['nova_features'][extension] = False
    return results


def display_results(results):
    for option in NOVA_EXTENSIONS.keys():
        config_value = getattr(CONF.compute_feature_enabled, option)
        if config_value != results['nova_features'][option]:
            print("Config option: %s should be changed to: %s" % (
                option, not config_value))


def main(argv):
    os = clients.ComputeAdminManager(interface='json')
    results = verify_extensions(os)
    verify_glance_api_versions(os)
    display_results(results)


if __name__ == "__main__":
    main(sys.argv)
