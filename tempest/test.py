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

import nose.plugins.attrib
import testresources
import testtools

from tempest import config
from tempest import manager

LOG = logging.getLogger(__name__)


def attr(*args, **kwargs):
    """A decorator which applies the nose and testtools attr decorator

    This decorator applies the nose attr decorator as well as the
    the testtools.testcase.attr if it is in the list of attributes
    to testtools we want to apply.
    """

    def decorator(f):
        testtool_attributes = ('smoke')

        if 'type' in kwargs and kwargs['type'] in testtool_attributes:
            return nose.plugins.attrib.attr(*args, **kwargs)(
                testtools.testcase.attr(kwargs['type'])(f))
        else:
            return nose.plugins.attrib.attr(*args, **kwargs)(f)

    return decorator


class BaseTestCase(testtools.TestCase,
                   testtools.testcase.WithAttributes,
                   testresources.ResourcedTestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        #NOTE(afazekas): inspection workaround
        BaseTestCase.config = config.TempestConfig()

    @classmethod
    def setUpClass(cls):
        if hasattr(super(BaseTestCase, cls), 'setUpClass'):
            super(BaseTestCase, cls).setUpClass()


class TestCase(BaseTestCase):
    """Base test case class for all Tempest tests

    Contains basic setup and convenience methods
    """

    manager_class = None

    @classmethod
    def setUpClass(cls):
        cls.manager = cls.manager_class()
        for attr_name in cls.manager.client_attr_names:
            # Ensure that pre-existing class attributes won't be
            # accidentally overriden.
            assert not hasattr(cls, attr_name)
            client = getattr(cls.manager, attr_name)
            setattr(cls, attr_name, client)
        cls.resource_keys = {}
        cls.os_resources = []

    def set_resource(self, key, thing):
        LOG.debug("Adding %r to shared resources of %s" %
                  (thing, self.__class__.__name__))
        self.resource_keys[key] = thing
        self.os_resources.append(thing)

    def get_resource(self, key):
        return self.resource_keys[key]

    def remove_resource(self, key):
        thing = self.resource_keys[key]
        self.os_resources.remove(thing)
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


def status_timeout(testcase, things, thing_id, expected_status):
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
            testcase.fail("%s failed to get to expected status."
                          "In ERROR state."
                          % thing)
        elif new_status == expected_status:
            return True  # All good.
        LOG.debug("Waiting for %s to get to %s status. "
                  "Currently in %s status",
                  thing, expected_status, new_status)
    conf = config.TempestConfig()
    if not call_until_true(check_status,
                           conf.compute.build_timeout,
                           conf.compute.build_interval):
        testcase.fail("Timed out waiting for thing %s to become %s"
                      % (thing_id, expected_status))


class DefaultClientSmokeTest(TestCase):

    """
    Base smoke test case class that provides the default clients to
    access the various OpenStack APIs.

    Smoke tests are tests that have the following characteristics:

     * Test basic operations of an API, typically in an order that
       a regular user would perform those operations
     * Test only the correct inputs and action paths -- no fuzz or
       random input data is sent, only valid inputs.
     * Use only the default client tool for calling an API
    """

    manager_class = manager.DefaultClientManager

    @classmethod
    def tearDownClass(cls):
        # NOTE(jaypipes): Because smoke tests are typically run in a specific
        # order, and because test methods in smoke tests generally create
        # resources in a particular order, we destroy resources in the reverse
        # order in which resources are added to the smoke test class object
        while cls.os_resources:
            thing = cls.os_resources.pop()
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))

            try:
                # OpenStack resources are assumed to have a delete()
                # method which destroys the resource...
                thing.delete()
            except Exception as e:
                # If the resource is already missing, mission accomplished.
                if e.__class__.__name__ == 'NotFound':
                    continue
                raise

            def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(thing, dict):
                    return True
                try:
                    thing.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    raise
                return False

            # Block until resource deletion has completed or timed-out
            call_until_true(is_deletion_complete, 10, 1)


class ComputeFuzzClientTest(TestCase):

    """
    Base test case class for OpenStack Compute API (Nova)
    that uses the Tempest REST fuzz client libs for calling the API.
    """

    manager_class = manager.ComputeFuzzClientManager
