# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

# Config
import ConfigParser
import os

# Default client libs
import keystoneclient.v2_0.client as keystone_client

# Import Openstack exceptions
import keystoneclient.exceptions as keystone_exception


DEFAULT_CONFIG_DIR = "%s/etc" % os.path.abspath(os.path.pardir)
DEFAULT_CONFIG_FILE = "tempest.conf"
DEFAULT_CONFIG_SAMPLE = "tempest.conf.sample"

# Environment variables override defaults
TEMPEST_CONFIG_DIR = os.environ.get('TEMPEST_CONFIG_DIR') or DEFAULT_CONFIG_DIR
TEMPEST_CONFIG = os.environ.get('TEMPEST_CONFIG') or "%s/%s" % \
    (TEMPEST_CONFIG_DIR, DEFAULT_CONFIG_FILE)
TEMPEST_CONFIG_SAMPLE = os.environ.get('TEMPEST_CONFIG_SAMPLE') or "%s/%s" % \
    (TEMPEST_CONFIG_DIR, DEFAULT_CONFIG_SAMPLE)

# Admin credentials
OS_USERNAME = os.environ.get('OS_USERNAME')
OS_PASSWORD = os.environ.get('OS_PASSWORD')
OS_TENANT_NAME = os.environ.get('OS_TENANT_NAME')
OS_AUTH_URL = os.environ.get('OS_AUTH_URL')

# Image references
IMAGE_ID = os.environ.get('IMAGE_ID')
IMAGE_ID_ALT = os.environ.get('IMAGE_ID_ALT')


class ClientManager(object):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """
    def __init__(self):
        self.identity_client = None
        self.image_client = None
        self.network_client = None
        self.compute_client = None
        self.volume_client = None

    def get_identity_client(self, **kwargs):
        """
        Returns the openstack identity python client
        :param username: a string representing the username
        :param password: a string representing the user's password
        :param tenant_name: a string representing the tenant name of the user
        :param auth_url: a string representing the auth url of the identity
        :param insecure: True if we wish to disable ssl certificate validation,
        False otherwise
        :returns an instance of openstack identity python client
        """
        if not self.identity_client:
            self.identity_client = keystone_client.Client(**kwargs)

        return self.identity_client


def getTempestConfigSample():
    """
    Gets the tempest configuration file as a ConfigParser object
    :return: the tempest configuration file
    """
    # get the sample config file from the sample
    config_sample = ConfigParser.ConfigParser()
    config_sample.readfp(open(TEMPEST_CONFIG_SAMPLE))

    return config_sample


def update_config_admin_credentials(config, config_section):
    """
    Updates the tempest config with the admin credentials
    :param config: an object representing the tempest config file
    :param config_section: the section name where the admin credentials are
    """
    # Check if credentials are present
    if not (OS_AUTH_URL and
            OS_USERNAME and
            OS_PASSWORD and
            OS_TENANT_NAME):
        raise Exception("Admin environment variables not found.")

    # TODO(tkammer): Add support for uri_v3
    config_identity_params = {'uri': OS_AUTH_URL,
                              'admin_username': OS_USERNAME,
                              'admin_password': OS_PASSWORD,
                              'admin_tenant_name': OS_TENANT_NAME}

    update_config_section_with_params(config,
                                      config_section,
                                      config_identity_params)


def update_config_section_with_params(config, section, params):
    """
    Updates a given config object with given params
    :param config: the object representing the config file of tempest
    :param section: the section we would like to update
    :param params: the parameters we wish to update for that section
    """
    for option, value in params.items():
        config.set(section, option, value)


def get_identity_client_kwargs(config, section_name):
    """
    Get the required arguments for the identity python client
    :param config: the tempest configuration file
    :param section_name: the section name in the configuration where the
    arguments can be found
    :return: a dictionary representing the needed arguments for the identity
    client
    """
    username = config.get(section_name, 'admin_username')
    password = config.get(section_name, 'admin_password')
    tenant_name = config.get(section_name, 'admin_tenant_name')
    auth_url = config.get(section_name, 'uri')
    dscv = config.get(section_name, 'disable_ssl_certificate_validation')
    kwargs = {'username': username,
              'password': password,
              'tenant_name': tenant_name,
              'auth_url': auth_url,
              'insecure': dscv}

    return kwargs


def create_user_with_tenant(identity_client, username, password, tenant_name):
    """
    Creates a user using a given identity client
    :param identity_client: openstack identity python client
    :param username: a string representing the username
    :param password: a string representing the user's password
    :param tenant_name: a string representing the tenant name of the user
    """
    # Try to create the necessary tenant
    tenant_id = None
    try:
        tenant_description = "Tenant for Tempest %s user" % username
        tenant = identity_client.tenants.create(tenant_name,
                                                tenant_description)
        tenant_id = tenant.id
    except keystone_exception.Conflict:

        # if already exist, use existing tenant
        tenant_list = identity_client.tenants.list()
        for tenant in tenant_list:
            if tenant.name == tenant_name:
                tenant_id = tenant.id

    # Try to create the user
    try:
        email = "%s@test.com" % username
        identity_client.users.create(name=username,
                                     password=password,
                                     email=email,
                                     tenant_id=tenant_id)
    except keystone_exception.Conflict:

        # if already exist, use existing user
        pass


def create_users_and_tenants(identity_client,
                             config,
                             identity_section):
    """
    Creates the two non admin users and tenants for tempest
    :param identity_client: openstack identity python client
    :param config: tempest configuration file
    :param identity_section: the section name of identity in the config
    """
    # Get the necessary params from the config file
    tenant_name = config.get(identity_section, 'tenant_name')
    username = config.get(identity_section, 'username')
    password = config.get(identity_section, 'password')

    alt_tenant_name = config.get(identity_section, 'alt_tenant_name')
    alt_username = config.get(identity_section, 'alt_username')
    alt_password = config.get(identity_section, 'alt_password')

    # Create the necessary users for the test runs
    create_user_with_tenant(identity_client, username, password, tenant_name)
    create_user_with_tenant(identity_client, alt_username, alt_password,
                            alt_tenant_name)


def main():
    """
    Main module to control the script
    """
    # TODO(tkammer): add support for existing config file
    config_sample = getTempestConfigSample()
    update_config_admin_credentials(config_sample, 'identity')

    client_manager = ClientManager()

    # Set the identity related info for tempest
    identity_client_kwargs = get_identity_client_kwargs(config_sample,
                                                        'identity')
    identity_client = client_manager.get_identity_client(
        **identity_client_kwargs)

    # Create the necessary users and tenants for tempest run
    create_users_and_tenants(identity_client,
                             config_sample,
                             'identity')

    # TODO(tkammer): add image implementation

if __name__ == "__main__":
    main()
