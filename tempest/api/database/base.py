# Copyright 2014 OpenStack Foundation
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
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseDatabaseTest(tempest.test.BaseTestCase):
    """Base test case class for all Database API tests."""

    _interface = 'json'
    force_tenant_isolation = False

    @classmethod
    def setUpClass(cls):
        super(BaseDatabaseTest, cls).setUpClass()
        if not CONF.service_available.trove:
            skip_msg = ("%s skipped as trove is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        cls.catalog_type = CONF.database.catalog_type
        cls.db_flavor_ref = CONF.database.db_flavor_ref
        cls.db_current_version = CONF.database.db_current_version

        os = cls.get_client_manager()
        cls.os = os
        cls.database_flavors_client = cls.os.database_flavors_client
        cls.os_flavors_client = cls.os.flavors_client
        cls.database_versions_client = cls.os.database_versions_client
