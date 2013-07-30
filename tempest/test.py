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

import os
import time

import nose.plugins.attrib
import testresources
import testtools

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)

# All the successful HTTP status codes from RFC 2616
HTTP_SUCCESS = (200, 201, 202, 203, 204, 205, 206)


def attr(*args, **kwargs):
    """A decorator which applies the nose and testtools attr decorator

    This decorator applies the nose attr decorator as well as the
    the testtools.testcase.attr if it is in the list of attributes
    to testtools we want to apply.
    """

    def decorator(f):
        if 'type' in kwargs and isinstance(kwargs['type'], str):
            f = testtools.testcase.attr(kwargs['type'])(f)
            if kwargs['type'] == 'smoke':
                f = testtools.testcase.attr('gate')(f)
        elif 'type' in kwargs and isinstance(kwargs['type'], list):
            for attr in kwargs['type']:
                f = testtools.testcase.attr(attr)(f)
                if attr == 'smoke':
                    f = testtools.testcase.attr('gate')(f)
        return nose.plugins.attrib.attr(*args, **kwargs)(f)

    return decorator


# there is a mis-match between nose and testtools for older pythons.
# testtools will set skipException to be either
# unittest.case.SkipTest, unittest2.case.SkipTest or an internal skip
# exception, depending on what it can find. Python <2.7 doesn't have
# unittest.case.SkipTest; so if unittest2 is not installed it falls
# back to the internal class.
#
# The current nose skip plugin will decide to raise either
# unittest.case.SkipTest or its own internal exception; it does not
# look for unittest2 or the internal unittest exception.  Thus we must
# monkey-patch testtools.TestCase.skipException to be the exception
# the nose skip plugin expects.
#
# However, with the switch to testr nose may not be available, so we
# require you to opt-in to this fix with an environment variable.
#
# This is temporary until upstream nose starts looking for unittest2
# as testtools does; we can then remove this and ensure unittest2 is
# available for older pythons; then nose and testtools will agree
# unittest2.case.SkipTest is the one-true skip test exception.
#
#   https://review.openstack.org/#/c/33056
#   https://github.com/nose-devs/nose/pull/699
if 'TEMPEST_PY26_NOSE_COMPAT' in os.environ:
    try:
        import unittest.case.SkipTest
        # convince pep8 we're using the import...
        if unittest.case.SkipTest:
            pass
        raise RuntimeError("You have unittest.case.SkipTest; "
                           "no need to override")
    except ImportError:
        LOG.info("Overriding skipException to nose SkipTest")
        testtools.TestCase.skipException = nose.plugins.skip.SkipTest


class BaseTestCase(testtools.TestCase,
                   testtools.testcase.WithAttributes,
                   testresources.ResourcedTestCase):

    config = config.TempestConfig()

    @classmethod
    def setUpClass(cls):
        if hasattr(super(BaseTestCase, cls), 'setUpClass'):
            super(BaseTestCase, cls).setUpClass()

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = clients.AdminManager(interface=cls._interface)
        admin_client = os.identity_client
        return admin_client

    @classmethod
    def _get_client_args(cls):

        return (
            cls.config,
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.uri
        )

    @classmethod
    def _get_isolated_creds(cls, admin=False):
        """
        Creates a new set of user/tenant/password credentials for a
        **regular** user of the Compute API so that a test case can
        operate in an isolated tenant container.
        """
        admin_client = cls._get_identity_admin_client()
        password = "pass"

        while True:
            try:
                rand_name_root = rand_name(cls.__name__)
                if cls.isolated_creds:
                # Main user already created. Create the alt or admin one...
                    if admin:
                        rand_name_root += '-admin'
                    else:
                        rand_name_root += '-alt'
                tenant_name = rand_name_root + "-tenant"
                tenant_desc = tenant_name + "-desc"

                resp, tenant = admin_client.create_tenant(
                    name=tenant_name, description=tenant_desc)
                break
            except exceptions.Duplicate:
                if cls.config.compute.allow_tenant_reuse:
                    tenant = admin_client.get_tenant_by_name(tenant_name)
                    LOG.info('Re-using existing tenant %s', tenant)
                    break

        while True:
            try:
                rand_name_root = rand_name(cls.__name__)
                if cls.isolated_creds:
                # Main user already created. Create the alt one...
                    rand_name_root += '-alt'
                username = rand_name_root + "-user"
                email = rand_name_root + "@example.com"
                resp, user = admin_client.create_user(username,
                                                      password,
                                                      tenant['id'],
                                                      email)
                break
            except exceptions.Duplicate:
                if cls.config.compute.allow_tenant_reuse:
                    user = admin_client.get_user_by_username(tenant['id'],
                                                             username)
                    LOG.info('Re-using existing user %s', user)
                    break
        # Store the complete creds (including UUID ids...) for later
        # but return just the username, tenant_name, password tuple
        # that the various clients will use.
        cls.isolated_creds.append((user, tenant))

        # Assign admin role if this is for admin creds
        if admin:
            _, roles = admin_client.list_roles()
            role = None
            try:
                _, roles = admin_client.list_roles()
                role = next(r for r in roles if r['name'] == 'admin')
            except StopIteration:
                msg = "No admin role found"
                raise exceptions.NotFound(msg)
            admin_client.assign_user_role(tenant['id'], user['id'], role['id'])

        return username, tenant_name, password

    @classmethod
    def _clear_isolated_creds(cls):
        if not cls.isolated_creds:
            return
        admin_client = cls._get_identity_admin_client()

        for user, tenant in cls.isolated_creds:
            admin_client.delete_user(user['id'])
            admin_client.delete_tenant(tenant['id'])


def call_until_true(func, duration, sleep_for):
    """
    Call the given function until it returns True (and return True) or
    until the specified duration (in seconds) elapses (and return
    False).

    :param func: A zero argument callable that returns True on success.
    :param duration: The number of seconds for which to attempt a
        successful call of the function.
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

    @classmethod
    def set_resource(cls, key, thing):
        LOG.debug("Adding %r to shared resources of %s" %
                  (thing, cls.__name__))
        cls.resource_keys[key] = thing
        cls.os_resources.append(thing)

    @classmethod
    def get_resource(cls, key):
        return cls.resource_keys[key]

    @classmethod
    def remove_resource(cls, key):
        thing = cls.resource_keys[key]
        cls.os_resources.remove(thing)
        del cls.resource_keys[key]

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
                self.fail("%s failed to get to expected status. "
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
            self.fail("Timed out waiting for thing %s to become %s"
                      % (thing_id, expected_status))
