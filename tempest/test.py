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
import time

import testtools

from tempest import manager

LOG = logging.getLogger(__name__)


class TestCase(testtools.TestCase):

    """
    Base test case class for all Tempest tests

    Contains basic setup and convenience methods
    """
    manager_class = None

    @classmethod
    def setUpClass(cls):
        cls.manager = cls.manager_class()
        cls.config = cls.manager.config
        for attr_name in cls.manager.client_attr_names:
            # Ensure that pre-existing class attributes won't be
            # accidentally overriden.
            assert not hasattr(cls, attr_name)
            client = getattr(cls.manager, attr_name)
            setattr(cls, attr_name, client)
        cls.resource_keys = {}
        cls.resources = []

    def set_resource(self, key, thing):
        LOG.debug("Adding %r to shared resources of %s" %
                  (thing, self.__class__.__name__))
        self.resource_keys[key] = thing
        self.resources.append(thing)

    def get_resource(self, key):
        return self.resource_keys[key]

    def remove_resource(self, key):
        thing = self.resource_keys[key]
        self.resources.remove(thing)
        del self.resource_keys[key]


def call_until_true(func, duration, sleep_for):
    """
    Call the given function until it returns True (and return True) or
    until the specified duration (in seconds) elapses (and return
    False).

    :param func: A zero argument callable that returns True on success.
    :param duration: The number of seconds for which to attempt a successful
                     call of the function.
    :param sleep_for: The number of seconds to sleep after an unsuccessful
                      invocation of the function.
    """
    now = time.time()
    timeout = now + duration
    while now < timeout:
        if func():
            return True
        LOG.debug("Sleeping for %d seconds", sleep_for)
        time.sleep(sleep_for)
        now = time.time()
    return False


class DefaultClientTest(TestCase):

    """
    Base test case class that provides the default clients to access
    the various OpenStack APIs.
    """

    manager_class = manager.DefaultClientManager

    def status_timeout(self, things, thing_id, expected_status):
        """
        Given a thing and an expected status, do a loop, sleeping
        for a configurable amount of time, checking for the
        expected status to show. At any time, if the returned
        status of the thing is ERROR, fail out.
        """
        def check_status():
            # python-novaclient has resources available to its client
            # that all implement a get() method taking an identifier
            # for the singular resource to retrieve.
            thing = things.get(thing_id)
            new_status = thing.status
            if new_status == 'ERROR':
                self.fail("%s failed to get to expected status."
                          "In ERROR state."
                          % thing)
            elif new_status == expected_status:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      thing, expected_status, new_status)
        if not call_until_true(check_status,
                               self.config.compute.build_timeout,
                               self.config.compute.build_interval):
            self.fail("Timed out waiting for thing %s to become %s"
                      % (thing_id, expected_status))


class ComputeFuzzClientTest(TestCase):

    """
    Base test case class for OpenStack Compute API (Nova)
    that uses the Tempest REST fuzz client libs for calling the API.
    """

    manager_class = manager.ComputeFuzzClientManager

    def status_timeout(self, client_get_method, thing_id, expected_status):
        """
        Given a method to get a resource and an expected status, do a loop,
        sleeping for a configurable amount of time, checking for the
        expected status to show. At any time, if the returned
        status of the thing is ERROR, fail out.

        :param client_get_method: The callable that will retrieve the thing
                                  with ID :param:thing_id
        :param thing_id: The ID of the thing to get
        :param expected_status: String value of the expected status of the
                                thing that we are looking for.

        :code ..

            Usage:

            def test_some_server_action(self):
                client = self.servers_client
                resp, server = client.create_server('random_server')
                self.status_timeout(client.get_server, server['id'], 'ACTIVE')
        """
        def check_status():
            # Tempest REST client has resources available to its client
            # that all implement a various get_$resource() methods taking
            # an identifier for the singular resource to retrieve.
            thing = client_get_method(thing_id)
            new_status = thing['status']
            if new_status == 'ERROR':
                self.fail("%s failed to get to expected status."
                          "In ERROR state."
                          % thing)
            elif new_status == expected_status:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      thing, expected_status, new_status)
        if not call_until_true(check_status,
                               self.config.compute.build_timeout,
                               self.config.compute.build_interval):
            self.fail("Timed out waiting for thing %s to become %s"
                      % (thing_id, expected_status))
