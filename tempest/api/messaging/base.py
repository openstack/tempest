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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils

from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseMessagingTest(test.BaseTestCase):

    """
    Base class for the Messaging tests that use the Tempest Zaqar REST client

    It is assumed that the following option is defined in the
    [service_available] section of etc/tempest.conf

        messaging as True
    """

    @classmethod
    def skip_checks(cls):
        super(BaseMessagingTest, cls).skip_checks()
        if not CONF.service_available.zaqar:
            raise cls.skipException("Zaqar support is required")

    @classmethod
    def setup_credentials(cls):
        super(BaseMessagingTest, cls).setup_credentials()
        cls.os = cls.get_client_manager()

    @classmethod
    def setup_clients(cls):
        super(BaseMessagingTest, cls).setup_clients()
        cls.client = cls.os.messaging_client

    @classmethod
    def resource_setup(cls):
        super(BaseMessagingTest, cls).resource_setup()
        cls.messaging_cfg = CONF.messaging

    @classmethod
    def create_queue(cls, queue_name):
        """Wrapper utility that returns a test queue."""
        resp, body = cls.client.create_queue(queue_name)
        return resp, body

    @classmethod
    def delete_queue(cls, queue_name):
        """Wrapper utility that deletes a test queue."""
        resp, body = cls.client.delete_queue(queue_name)
        return resp, body

    @classmethod
    def check_queue_exists(cls, queue_name):
        """Wrapper utility that checks the existence of a test queue."""
        resp, body = cls.client.get_queue(queue_name)
        return resp, body

    @classmethod
    def check_queue_exists_head(cls, queue_name):
        """Wrapper utility checks the head of a queue via http HEAD."""
        resp, body = cls.client.head_queue(queue_name)
        return resp, body

    @classmethod
    def list_queues(cls):
        """Wrapper utility that lists queues."""
        resp, body = cls.client.list_queues()
        return resp, body

    @classmethod
    def get_queue_stats(cls, queue_name):
        """Wrapper utility that returns the queue stats."""
        resp, body = cls.client.get_queue_stats(queue_name)
        return resp, body

    @classmethod
    def get_queue_metadata(cls, queue_name):
        """Wrapper utility that gets a queue metadata."""
        resp, body = cls.client.get_queue_metadata(queue_name)
        return resp, body

    @classmethod
    def set_queue_metadata(cls, queue_name, rbody):
        """Wrapper utility that sets the metadata of a queue."""
        resp, body = cls.client.set_queue_metadata(queue_name, rbody)
        return resp, body

    @classmethod
    def post_messages(cls, queue_name, rbody):
        """Wrapper utility that posts messages to a queue."""
        resp, body = cls.client.post_messages(queue_name, rbody)

        return resp, body

    @classmethod
    def list_messages(cls, queue_name):
        """Wrapper utility that lists the messages in a queue."""
        resp, body = cls.client.list_messages(queue_name)

        return resp, body

    @classmethod
    def get_single_message(cls, message_uri):
        """Wrapper utility that gets a single message."""
        resp, body = cls.client.get_single_message(message_uri)

        return resp, body

    @classmethod
    def get_multiple_messages(cls, message_uri):
        """Wrapper utility that gets multiple messages."""
        resp, body = cls.client.get_multiple_messages(message_uri)

        return resp, body

    @classmethod
    def delete_messages(cls, message_uri):
        """Wrapper utility that deletes messages."""
        resp, body = cls.client.delete_messages(message_uri)

        return resp, body

    @classmethod
    def post_claims(cls, queue_name, rbody, url_params=False):
        """Wrapper utility that claims messages."""
        resp, body = cls.client.post_claims(
            queue_name, rbody, url_params=False)

        return resp, body

    @classmethod
    def query_claim(cls, claim_uri):
        """Wrapper utility that gets a claim."""
        resp, body = cls.client.query_claim(claim_uri)

        return resp, body

    @classmethod
    def update_claim(cls, claim_uri, rbody):
        """Wrapper utility that updates a claim."""
        resp, body = cls.client.update_claim(claim_uri, rbody)

        return resp, body

    @classmethod
    def release_claim(cls, claim_uri):
        """Wrapper utility that deletes a claim."""
        resp, body = cls.client.release_claim(claim_uri)

        return resp, body

    @classmethod
    def generate_message_body(cls, repeat=1):
        """Wrapper utility that sets the metadata of a queue."""
        message_ttl = data_utils.\
            rand_int_id(start=60, end=CONF.messaging.max_message_ttl)

        key = data_utils.arbitrary_string(size=20, base_text='MessagingKey')
        value = data_utils.arbitrary_string(size=20,
                                            base_text='MessagingValue')
        message_body = {key: value}

        rbody = ([{'body': message_body, 'ttl': message_ttl}] * repeat)
        return rbody
