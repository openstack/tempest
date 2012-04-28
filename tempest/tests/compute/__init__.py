# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import logging

import nose

from tempest import config
from tempest import openstack

LOG = logging.getLogger(__name__)

CONFIG = config.TempestConfig()
CREATE_IMAGE_ENABLED = CONFIG.compute.create_image_enabled
RESIZE_AVAILABLE = CONFIG.compute.resize_available
CHANGE_PASSWORD_AVAILABLE = CONFIG.compute.change_password_available
WHITEBOX_ENABLED = CONFIG.compute.whitebox_enabled
DISK_CONFIG_ENABLED = False
FLAVOR_EXTRA_DATA_ENABLED = False
MULTI_USER = False


# All compute tests -- single setup function
def setup_package():
    LOG.debug("Entering tempest.tests.compute.setup_package")

    global MULTI_USER, DISK_CONFIG_ENABLED, FLAVOR_EXTRA_DATA_ENABLED
    os = openstack.Manager()
    images_client = os.images_client
    flavors_client = os.flavors_client
    extensions_client = os.extensions_client
    DISK_CONFIG_ENABLED = extensions_client.is_enabled('DiskConfig')
    FLAVOR_EXTRA_DATA_ENABLED = extensions_client.is_enabled('FlavorExtraData')

    # Validate reference data exists
    # If not, we raise the exception here and prevent
    # going forward...
    try:
        image_ref = CONFIG.compute.image_ref
        image_ref_alt = CONFIG.compute.image_ref_alt
        images_client.get_image(image_ref)
        images_client.get_image(image_ref_alt)

        flavor_ref = CONFIG.compute.flavor_ref
        flavor_ref_alt = CONFIG.compute.flavor_ref_alt
        flavors_client.get_flavor_details(flavor_ref)
        flavors_client.get_flavor_details(flavor_ref_alt)
    except Exception as e:
        msg = "Failed basic configuration: %s" % e
        raise nose.SkipTest(msg)

    # Determine if there are two regular users that can be
    # used in testing. If the test cases are allowed to create
    # users (config.compute.allow_tenant_isolation is true,
    # then we allow multi-user.
    if CONFIG.compute.allow_tenant_isolation:
        MULTI_USER = True
    else:
        user1 = CONFIG.compute.username
        user2 = CONFIG.compute.alt_username
        if user2 and user1 != user2:
            user2_password = CONFIG.compute.alt_password
            user2_tenant_name = CONFIG.compute.alt_tenant_name
            if not user2_password or not user2_tenant_name:
                msg = ("Alternate user specified but not alternate "
                       "tenant or password")
                raise nose.SkipTest(msg)
            MULTI_USER = True
