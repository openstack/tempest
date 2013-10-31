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

from tempest import config
from tempest.exceptions import InvalidConfiguration
from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)

CONFIG = config.TempestConfig()
CREATE_IMAGE_ENABLED = CONFIG.compute_feature_enabled.create_image
RESIZE_AVAILABLE = CONFIG.compute_feature_enabled.resize
CHANGE_PASSWORD_AVAILABLE = CONFIG.compute_feature_enabled.change_password
DISK_CONFIG_ENABLED = CONFIG.compute_feature_enabled.disk_config
FLAVOR_EXTRA_DATA_ENABLED = CONFIG.compute_feature_enabled.flavor_extra
MULTI_USER = True


# All compute tests -- single setup function
def generic_setup_package():
    LOG.debug("Entering tempest.api.compute.setup_package")

    global MULTI_USER

    # Determine if there are two regular users that can be
    # used in testing. If the test cases are allowed to create
    # users (config.compute.allow_tenant_isolation is true,
    # then we allow multi-user.
    if not CONFIG.compute.allow_tenant_isolation:
        user1 = CONFIG.identity.username
        user2 = CONFIG.identity.alt_username
        if not user2 or user1 == user2:
            MULTI_USER = False
        else:
            user2_password = CONFIG.identity.alt_password
            user2_tenant_name = CONFIG.identity.alt_tenant_name
            if not user2_password or not user2_tenant_name:
                msg = ("Alternate user specified but not alternate "
                       "tenant or password: alt_tenant_name=%s alt_password=%s"
                       % (user2_tenant_name, user2_password))
                raise InvalidConfiguration(msg)
