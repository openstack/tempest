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
#
# This script aims to configure an initial Openstack environment with all the
# necessary configurations for tempest's run using nothing but Openstack's
# native API.
# That includes, creating users, tenants, registering images (cirros),
# configuring neutron and so on.
#
# ASSUMPTION: this script is run by an admin user as it is meant to configure
# the Openstack environment prior to actual use.

# Config
import ConfigParser
import os
import tarfile
import urllib2

# Default client libs
import glanceclient as glance_client
import keystoneclient.v2_0.client as keystone_client

# Import Openstack exceptions
import glanceclient.exc as glance_exception
import keystoneclient.exceptions as keystone_exception


TEMPEST_TEMP_DIR = os.getenv("TEMPEST_TEMP_DIR", "/tmp").rstrip('/')
TEMPEST_ROOT_DIR = os.getenv("TEMPEST_ROOT_DIR", os.getenv("HOME")).rstrip('/')

# Environment variables override defaults
TEMPEST_CONFIG_DIR = os.getenv("TEMPEST_CONFIG_DIR",
                               "%s%s" % (TEMPEST_ROOT_DIR, "/etc")).rstrip('/')
TEMPEST_CONFIG_FILE = os.getenv("TEMPEST_CONFIG_FILE",
                                "%s%s" % (TEMPEST_CONFIG_DIR, "/tempest.conf"))
TEMPEST_CONFIG_SAMPLE = os.getenv("TEMPEST_CONFIG_SAMPLE",
                                  "%s%s" % (TEMPEST_CONFIG_DIR,
                                            "/tempest.conf.sample"))
# Image references
IMAGE_DOWNLOAD_CHUNK_SIZE = 8 * 1024
IMAGE_UEC_SOURCE_URL = os.getenv("IMAGE_UEC_SOURCE_URL",
                                 "http://download.cirros-cloud.net/0.3.1/"
                                 "cirros-0.3.1-x86_64-uec.tar.gz")
TEMPEST_IMAGE_ID = os.getenv('IMAGE_ID')
TEMPEST_IMAGE_ID_ALT = os.getenv('IMAGE_ID_ALT')
IMAGE_STATUS_ACTIVE = 'active'


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

    def get_image_client(self, version="1", *args, **kwargs):
        """
        This method returns Openstack glance python client
        :param version: a string representing the version of the glance client
        to use.
        :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
        :param string token: Token for authentication.
        :param integer timeout: Allows customization of the timeout for client
                                http requests. (optional)
        :return: a Client object representing the glance client
        """
        if not self.image_client:
            self.image_client = glance_client.Client(version, *args, **kwargs)

        return self.image_client


def get_tempest_config(path_to_config):
    """
    Gets the tempest configuration file as a ConfigParser object
    :param path_to_config: path to the config file
    :return: a ConfigParser object representing the tempest configuration file
    """
    # get the sample config file from the sample
    config = ConfigParser.ConfigParser()
    config.readfp(open(path_to_config))

    return config


def update_config_admin_credentials(config, config_section):
    """
    Updates the tempest config with the admin credentials
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section name where the admin credentials are
    """
    # Check if credentials are present, default uses the config credentials
    OS_USERNAME = os.getenv('OS_USERNAME',
                            config.get(config_section, "admin_username"))
    OS_PASSWORD = os.getenv('OS_PASSWORD',
                            config.get(config_section, "admin_password"))
    OS_TENANT_NAME = os.getenv('OS_TENANT_NAME',
                               config.get(config_section, "admin_tenant_name"))
    OS_AUTH_URL = os.getenv('OS_AUTH_URL', config.get(config_section, "uri"))

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


def update_config_section_with_params(config, config_section, params):
    """
    Updates a given config object with given params
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section we would like to update
    :param params: the parameters we wish to update for that section
    """
    for option, value in params.items():
        config.set(config_section, option, value)


def get_identity_client_kwargs(config, config_section):
    """
    Get the required arguments for the identity python client
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section name in the configuration where the
    arguments can be found
    :return: a dictionary representing the needed arguments for the identity
    client
    """
    username = config.get(config_section, 'admin_username')
    password = config.get(config_section, 'admin_password')
    tenant_name = config.get(config_section, 'admin_tenant_name')
    auth_url = config.get(config_section, 'uri')
    dscv = config.get(config_section, 'disable_ssl_certificate_validation')
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
                             config_section):
    """
    Creates the two non admin users and tenants for tempest
    :param identity_client: openstack identity python client
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section name of identity in the config
    """
    # Get the necessary params from the config file
    tenant_name = config.get(config_section, 'tenant_name')
    username = config.get(config_section, 'username')
    password = config.get(config_section, 'password')

    alt_tenant_name = config.get(config_section, 'alt_tenant_name')
    alt_username = config.get(config_section, 'alt_username')
    alt_password = config.get(config_section, 'alt_password')

    # Create the necessary users for the test runs
    create_user_with_tenant(identity_client, username, password, tenant_name)
    create_user_with_tenant(identity_client, alt_username, alt_password,
                            alt_tenant_name)


def get_image_client_kwargs(identity_client, config, config_section):
    """
    Get the required arguments for the image python client
    :param identity_client: openstack identity python client
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section name of identity in the config
    :return: a dictionary representing the needed arguments for the image
    client
    """

    token = identity_client.auth_token
    endpoint = identity_client.\
        service_catalog.url_for(service_type='image', endpoint_type='publicURL'
                                )
    dscv = config.get(config_section, 'disable_ssl_certificate_validation')
    kwargs = {'endpoint': endpoint,
              'token': token,
              'insecure': dscv}

    return kwargs


def images_exist(image_client):
    """
    Checks whether the images ID's located in the environment variable are
    indeed registered
    :param image_client: the openstack python client representing the image
    client
    """
    exist = True
    if not TEMPEST_IMAGE_ID or not TEMPEST_IMAGE_ID_ALT:
        exist = False
    else:
        try:
            image_client.images.get(TEMPEST_IMAGE_ID)
            image_client.images.get(TEMPEST_IMAGE_ID_ALT)
        except glance_exception.HTTPNotFound:
            exist = False

    return exist


def download_and_register_uec_images(image_client, download_url,
                                     download_folder):
    """
    Downloads and registered the UEC AKI/AMI/ARI images
    :param image_client:
    :param download_url: the url of the uec tar file
    :param download_folder: the destination folder we wish to save the file to
    """
    basename = os.path.basename(download_url)
    path = os.path.join(download_folder, basename)

    request = urllib2.urlopen(download_url)

    # First, download the file
    with open(path, "wb") as fp:
        while True:
            chunk = request.read(IMAGE_DOWNLOAD_CHUNK_SIZE)
            if not chunk:
                break

            fp.write(chunk)

    # Then extract and register images
    tar = tarfile.open(path, "r")
    for name in tar.getnames():
        file_obj = tar.extractfile(name)
        format = "aki"

        if file_obj.name.endswith(".img"):
            format = "ami"

        if file_obj.name.endswith("initrd"):
            format = "ari"

        # Register images in image client
        image_client.images.create(name=file_obj.name, disk_format=format,
                                   container_format=format, data=file_obj,
                                   is_public="true")

    tar.close()


def create_images(image_client, config, config_section,
                  download_url=IMAGE_UEC_SOURCE_URL,
                  download_folder=TEMPEST_TEMP_DIR):
    """
    Creates images for tempest's use and registers the environment variables
    IMAGE_ID and IMAGE_ID_ALT with registered images
    :param image_client: Openstack python image client
    :param config: a ConfigParser object representing the tempest config file
    :param config_section: the section name where the IMAGE ids are set
    :param download_url: the URL from which we should download the UEC tar
    :param download_folder: the place where we want to save the download file
    """
    if not images_exist(image_client):
        # Falls down to the default uec images
        download_and_register_uec_images(image_client, download_url,
                                         download_folder)
        image_ids = []
        for image in image_client.images.list():
            image_ids.append(image.id)

        os.environ["IMAGE_ID"] = image_ids[0]
        os.environ["IMAGE_ID_ALT"] = image_ids[1]

    params = {'image_ref': os.getenv("IMAGE_ID"),
              'image_ref_alt': os.getenv("IMAGE_ID_ALT")}

    update_config_section_with_params(config, config_section, params)


def main():
    """
    Main module to control the script
    """
    # Check if config file exists or fall to the default sample otherwise
    path_to_config = TEMPEST_CONFIG_SAMPLE

    if os.path.isfile(TEMPEST_CONFIG_FILE):
        path_to_config = TEMPEST_CONFIG_FILE

    config = get_tempest_config(path_to_config)
    update_config_admin_credentials(config, 'identity')

    client_manager = ClientManager()

    # Set the identity related info for tempest
    identity_client_kwargs = get_identity_client_kwargs(config,
                                                        'identity')
    identity_client = client_manager.get_identity_client(
        **identity_client_kwargs)

    # Create the necessary users and tenants for tempest run
    create_users_and_tenants(identity_client, config, 'identity')

    # Set the image related info for tempest
    image_client_kwargs = get_image_client_kwargs(identity_client,
                                                  config,
                                                  'identity')
    image_client = client_manager.get_image_client(**image_client_kwargs)

    # Create the necessary users and tenants for tempest run
    create_images(image_client, config, 'compute')

    # TODO(tkammer): add network implementation

if __name__ == "__main__":
    main()
