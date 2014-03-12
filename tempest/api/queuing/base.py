# Copyright (c) 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseQueuingTest(test.BaseTestCase):

    """
    Base class for the Queuing tests that use the Tempest Marconi REST client

    It is assumed that the following option is defined in the
    [service_available] section of etc/tempest.conf

        queuing as True
    """

    @classmethod
    def setUpClass(cls):
        super(BaseQueuingTest, cls).setUpClass()
        if not CONF.service_available.marconi:
            raise cls.skipException("Marconi support is required")
        os = cls.get_client_manager()
        cls.queuing_cfg = CONF.queuing
        cls.client = os.queuing_client

    @classmethod
    def create_queue(cls, queue_name):
        """Wrapper utility that returns a test queue."""
        resp, body = cls.client.create_queue(queue_name)
        return resp, body
