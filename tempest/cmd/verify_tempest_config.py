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

"""
Verifies user's current tempest configuration.

This command is used for updating or user's tempest configuration file based on
api queries or replacing all option in a tempest configuration file for a full
list of extensions.

General Options
===============

-u, --update
------------
Update the config file with results from api queries. This assumes whatever is
set in the config file is incorrect.

-o FILE, --output=FILE
----------------------
Output file to write an updated config file to. This has to be a separate file
from the original one. If one isn't specified with -u the values which should
be changed will be printed to STDOUT.

-r, --replace-ext
-----------------
If specified the all option will be replaced with a full list of extensions.

Environment Variables
=====================

The command is workspace aware - it uses tempest config file tempest.conf
located in ./etc/ directory.
The path to the config file and it's name can be changed through environment
variables.

TEMPEST_CONFIG_DIR
------------------
Path to a directory where tempest configuration file is stored. If the variable
is set, the default path (./etc/) is overridden.

TEMPEST_CONFIG
--------------
Name of a tempest configuration file. If the variable is specified, the default
name (tempest.conf) is overridden.

"""

import argparse
import os
import re
import sys
import traceback

from cliff import command
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
from six import moves
from six.moves.urllib import parse as urlparse

from tempest import clients
from tempest.common import credentials_factory as credentials
from tempest import config
import tempest.lib.common.http
from tempest.lib import exceptions as lib_exc


CONF = config.CONF
CONF_PARSER = None

LOG = logging.getLogger(__name__)


def _get_config_file():
    config_dir = os.getcwd()
    default_config_dir = os.path.join(config_dir, "etc")
    default_config_file = "tempest.conf"

    conf_dir = os.environ.get('TEMPEST_CONFIG_DIR', default_config_dir)
    conf_file = os.environ.get('TEMPEST_CONFIG', default_config_file)
    path = os.path.join(conf_dir, conf_file)
    fd = open(path, 'r+')
    return fd


def change_option(option, group, value):
    if not CONF_PARSER.has_section(group):
        CONF_PARSER.add_section(group)
    CONF_PARSER.set(group, option, str(value))


def print_and_or_update(option, group, value, update):
    print('Config option %s in group %s should be changed to: %s'
          % (option, group, value))
    if update:
        change_option(option, group, value)


def contains_version(prefix, versions):
    return any([x for x in versions if x.startswith(prefix)])


def verify_glance_api_versions(os, update):
    # Check glance api versions
    # Since we want to verify that the configuration is correct, we cannot
    # rely on a specific version of the API being available.
    try:
        _, versions = os.image_v1.ImagesClient().get_versions()
    except lib_exc.NotFound:
        # If not found, we use v2. The assumption is that either v1 or v2
        # are available, since glance is marked as available in the catalog.
        # If not, glance should be disabled in Tempest conf.
        try:
            versions = os.image_v2.VersionsClient().list_versions()['versions']
            versions = [x['id'] for x in versions]
        except lib_exc.NotFound:
            msg = ('Glance is available in the catalog, but no known version, '
                   '(v1.x or v2.x) of Glance could be found, so Glance should '
                   'be configured as not available')
            LOG.warn(msg)
            print_and_or_update('glance', 'service-available', False, update)
            return

    if CONF.image_feature_enabled.api_v1 != contains_version('v1.', versions):
        print_and_or_update('api_v1', 'image-feature-enabled',
                            not CONF.image_feature_enabled.api_v1, update)
    if CONF.image_feature_enabled.api_v2 != contains_version('v2.', versions):
        print_and_or_update('api_v2', 'image-feature-enabled',
                            not CONF.image_feature_enabled.api_v2, update)


def _remove_version_project(url_path):
    # The regex matches strings like /v2.0, /v3/, /v2.1/project-id/
    return re.sub(r'/v\d+(\.\d+)?(/[^/]+)?', '', url_path)


def _get_unversioned_endpoint(base_url):
    endpoint_parts = urlparse.urlparse(base_url)
    new_path = _remove_version_project(endpoint_parts.path)
    endpoint_parts = endpoint_parts._replace(path=new_path)
    endpoint = urlparse.urlunparse(endpoint_parts)
    return endpoint


def _get_api_versions(os, service):
    # Clients are used to obtain the base_url. Each client applies the
    # appropriate filters to the catalog to extract a base_url which
    # matches the configured region and endpoint_type.
    # The base URL is used to obtain the list of versions available.
    client_dict = {
        'nova': os.compute.ServersClient(),
        'keystone': os.identity_v3.IdentityClient(
            endpoint_type=CONF.identity.v3_endpoint_type),
        'cinder': os.volume_v3.VolumesClient(),
    }
    if service != 'keystone' and service != 'cinder':
        # Since keystone and cinder may be listening on a path,
        # do not remove the path.
        client_dict[service].skip_path()
    endpoint = _get_unversioned_endpoint(client_dict[service].base_url)

    http = tempest.lib.common.http.ClosingHttp(
        CONF.identity.disable_ssl_certificate_validation,
        CONF.identity.ca_certificates_file)

    __, body = http.request(endpoint, 'GET')
    client_dict[service].reset_path()
    try:
        body = json.loads(body)
    except ValueError:
        LOG.error(
            'Failed to get a JSON response from unversioned endpoint %s '
            '(versioned endpoint was %s). Response is:\n%s',
            endpoint, client_dict[service].base_url, body[:100])
        raise
    if service == 'keystone':
        versions = map(lambda x: x['id'], body['versions']['values'])
    else:
        versions = map(lambda x: x['id'], body['versions'])
    return list(versions)


def verify_keystone_api_versions(os, update):
    # Check keystone api versions
    versions = _get_api_versions(os, 'keystone')
    if (CONF.identity_feature_enabled.api_v3 !=
            contains_version('v3.', versions)):
        print_and_or_update('api_v3', 'identity-feature-enabled',
                            not CONF.identity_feature_enabled.api_v3, update)


def verify_cinder_api_versions(os, update):
    # Check cinder api versions
    versions = _get_api_versions(os, 'cinder')
    if (CONF.volume_feature_enabled.api_v1 !=
            contains_version('v1.', versions)):
        print_and_or_update('api_v1', 'volume-feature-enabled',
                            not CONF.volume_feature_enabled.api_v1, update)
    if (CONF.volume_feature_enabled.api_v2 !=
            contains_version('v2.', versions)):
        print_and_or_update('api_v2', 'volume-feature-enabled',
                            not CONF.volume_feature_enabled.api_v2, update)
    if (CONF.volume_feature_enabled.api_v3 !=
            contains_version('v3.', versions)):
        print_and_or_update('api_v3', 'volume-feature-enabled',
                            not CONF.volume_feature_enabled.api_v3, update)


def verify_api_versions(os, service, update):
    verify = {
        'cinder': verify_cinder_api_versions,
        'glance': verify_glance_api_versions,
        'keystone': verify_keystone_api_versions,
    }
    if service not in verify:
        return
    verify[service](os, update)


def get_extension_client(os, service):
    extensions_client = {
        'nova': os.compute.ExtensionsClient(),
        'neutron': os.network.ExtensionsClient(),
        'swift': os.object_storage.CapabilitiesClient(),
        # NOTE: Cinder v3 API is current and v2 and v1 are deprecated.
        # V3 extension API is the same as v2, so we reuse the v2 client
        # for v3 API also.
        'cinder': os.volume_v2.ExtensionsClient(),
    }

    if service not in extensions_client:
        print('No tempest extensions client for %s' % service)
        sys.exit(1)
    return extensions_client[service]


def get_enabled_extensions(service):
    extensions_options = {
        'nova': CONF.compute_feature_enabled.api_extensions,
        'cinder': CONF.volume_feature_enabled.api_extensions,
        'neutron': CONF.network_feature_enabled.api_extensions,
        'swift': CONF.object_storage_feature_enabled.discoverable_apis,
    }
    if service not in extensions_options:
        print('No supported extensions list option for %s' % service)
        sys.exit(1)
    return extensions_options[service]


def verify_extensions(os, service, results):
    extensions_client = get_extension_client(os, service)
    if service != 'swift':
        resp = extensions_client.list_extensions()
    else:
        resp = extensions_client.list_capabilities()
    # For Nova, Cinder and Neutron we use the alias name rather than the
    # 'name' field because the alias is considered to be the canonical
    # name.
    if isinstance(resp, dict):
        if service == 'swift':
            # Remove Swift general information from extensions list
            resp.pop('swift')
            extensions = resp.keys()
        else:
            extensions = map(lambda x: x['alias'], resp['extensions'])

    else:
        extensions = map(lambda x: x['alias'], resp)
    extensions = list(extensions)
    if not results.get(service):
        results[service] = {}
    extensions_opt = get_enabled_extensions(service)
    if extensions_opt[0] == 'all':
        results[service]['extensions'] = extensions
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


def display_results(results, update, replace):
    update_dict = {
        'swift': 'object-storage-feature-enabled',
        'nova': 'compute-feature-enabled',
        'cinder': 'volume-feature-enabled',
        'neutron': 'network-feature-enabled',
    }
    for service in results:
        # If all extensions are specified as being enabled there is no way to
        # verify this so we just assume this to be true
        if results[service].get('extensions'):
            if replace:
                output_list = results[service].get('extensions')
            else:
                output_list = ['all']
        else:
            extension_list = get_enabled_extensions(service)
            output_list = []
            for extension in results[service]:
                if not results[service][extension]:
                    if extension in extension_list:
                        print("%s extension: %s should not be included in the "
                              "list of enabled extensions" % (service,
                                                              extension))
                    else:
                        print("%s extension: %s should be included in the list"
                              " of enabled extensions" % (service, extension))
                        output_list.append(extension)
                else:
                    output_list.append(extension)
        if update:
            # Sort List
            output_list.sort()
            # Convert list to a string
            output_string = ', '.join(output_list)
            if service == 'swift':
                change_option('discoverable_apis', update_dict[service],
                              output_string)
            else:
                change_option('api_extensions', update_dict[service],
                              output_string)


def check_service_availability(os, update):
    services = []
    avail_services = []
    codename_match = {
        'volume': 'cinder',
        'network': 'neutron',
        'image': 'glance',
        'object_storage': 'swift',
        'compute': 'nova',
        'baremetal': 'ironic',
        'identity': 'keystone',
    }
    # Get catalog list for endpoints to use for validation
    _token, auth_data = os.auth_provider.get_auth()
    if os.auth_version == 'v2':
        catalog_key = 'serviceCatalog'
    else:
        catalog_key = 'catalog'
    for entry in auth_data[catalog_key]:
        services.append(entry['type'])
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
                    if update:
                        change_option(codename_match[cfgname],
                                      'service_available', False)
            else:
                if not getattr(CONF.service_available,
                               codename_match[cfgname]):
                    print('Endpoint type %s is available, service %s should be'
                          ' set as available in the config file.' % (
                              catalog_type, codename_match[cfgname]))
                    if update:
                        change_option(codename_match[cfgname],
                                      'service_available', True)
                        # If we are going to enable this we should allow
                        # extension checks.
                        avail_services.append(codename_match[cfgname])
                else:
                    avail_services.append(codename_match[cfgname])
    return avail_services


def _parser_add_args(parser):
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update the config file with results from api '
                             'queries. This assumes whatever is set in the '
                             'config file is incorrect. In the case of '
                             'endpoint checks where it could either be the '
                             'incorrect catalog type or the service available '
                             'option the service available option is assumed '
                             'to be incorrect and is thus changed')
    parser.add_argument('-o', '--output',
                        help="Output file to write an updated config file to. "
                             "This has to be a separate file from the "
                             "original config file. If one isn't specified "
                             "with -u the values which should be changed "
                             "will be printed to STDOUT")
    parser.add_argument('-r', '--replace-ext', action='store_true',
                        help="If specified the all option will be replaced "
                             "with a full list of extensions")


def parse_args():
    parser = argparse.ArgumentParser()
    _parser_add_args(parser)
    opts = parser.parse_args()
    return opts


def main(opts=None):
    print('Running config verification...')
    if opts is None:
        print("Use of: 'verify-tempest-config' is deprecated, "
              "please use: 'tempest verify-config'")
        opts = parse_args()
    update = opts.update
    replace = opts.replace_ext
    global CONF_PARSER

    if update:
        conf_file = _get_config_file()
        CONF_PARSER = moves.configparser.ConfigParser()
        CONF_PARSER.optionxform = str
        CONF_PARSER.readfp(conf_file)

    # Indicate not to create network resources as part of getting credentials
    net_resources = {
        'network': False,
        'router': False,
        'subnet': False,
        'dhcp': False
    }
    icreds = credentials.get_credentials_provider(
        'verify_tempest_config', network_resources=net_resources)
    try:
        os = clients.Manager(icreds.get_primary_creds().credentials)
        services = check_service_availability(os, update)
        results = {}
        for service in ['nova', 'cinder', 'neutron', 'swift']:
            if service not in services:
                continue
            results = verify_extensions(os, service, results)

        # Verify API versions of all services in the keystone catalog and
        # keystone itself.
        services.append('keystone')
        for service in services:
            verify_api_versions(os, service, update)

        display_results(results, update, replace)
        if update:
            conf_file.close()
            if opts.output:
                with open(opts.output, 'w+') as outfile:
                    CONF_PARSER.write(outfile)
    finally:
        icreds.clear_creds()


class TempestVerifyConfig(command.Command):
    """Verify your current tempest configuration"""

    def get_parser(self, prog_name):
        parser = super(TempestVerifyConfig, self).get_parser(prog_name)
        _parser_add_args(parser)
        return parser

    def take_action(self, parsed_args):
        try:
            main(parsed_args)
        except Exception:
            LOG.exception("Failure verifying configuration.")
            traceback.print_exc()
            raise

if __name__ == "__main__":
    main()
