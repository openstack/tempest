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

from oslo_log import log as logging

from tempest import config
import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseDatabaseTest(tempest.test.BaseTestCase):
    """Base test case class for all Database API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseDatabaseTest, cls).skip_checks()
        if not CONF.service_available.trove:
            skip_msg = ("%s skipped as trove is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        super(BaseDatabaseTest, cls).setup_credentials()
        cls.os = cls.get_client_manager()

    @classmethod
    def setup_clients(cls):
        super(BaseDatabaseTest, cls).setup_clients()
        cls.database_flavors_client = cls.os.database_flavors_client
        cls.os_flavors_client = cls.os.flavors_client
        cls.database_limits_client = cls.os.database_limits_client
        cls.database_versions_client = cls.os.database_versions_client

    @classmethod
    def resource_setup(cls):
        super(BaseDatabaseTest, cls).resource_setup()

        cls.catalog_type = CONF.database.catalog_type
        cls.db_flavor_ref = CONF.database.db_flavor_ref
        cls.db_current_version = CONF.database.db_current_version
