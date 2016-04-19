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

import atexit
import functools
import os
import re
import sys
import time

import fixtures
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
from oslo_utils import importutils
import six
from six.moves import urllib
import testscenarios
import testtools

from tempest import clients
from tempest.common import cred_client
from tempest.common import credentials_factory as credentials
from tempest.common import fixed_network
import tempest.common.generator.valid_generator as valid
import tempest.common.validation_resources as vresources
from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

LOG = logging.getLogger(__name__)

CONF = config.CONF

idempotent_id = decorators.idempotent_id


def attr(**kwargs):
    """A decorator which applies the testtools attr decorator

    This decorator applies the testtools.testcase.attr if it is in the list of
    attributes to testtools we want to apply.
    """

    def decorator(f):
        if 'type' in kwargs and isinstance(kwargs['type'], str):
            f = testtools.testcase.attr(kwargs['type'])(f)
        elif 'type' in kwargs and isinstance(kwargs['type'], list):
            for attr in kwargs['type']:
                f = testtools.testcase.attr(attr)(f)
        return f

    return decorator


def get_service_list():
    service_list = {
        'compute': CONF.service_available.nova,
        'image': CONF.service_available.glance,
        'baremetal': CONF.service_available.ironic,
        'volume': CONF.service_available.cinder,
        'orchestration': CONF.service_available.heat,
        # NOTE(mtreinish) nova-network will provide networking functionality
        # if neutron isn't available, so always set to True.
        'network': True,
        'identity': True,
        'object_storage': CONF.service_available.swift,
        'dashboard': CONF.service_available.horizon,
        'telemetry': CONF.service_available.ceilometer,
        'data_processing': CONF.service_available.sahara,
        'database': CONF.service_available.trove
    }
    return service_list


def services(*args):
    """A decorator used to set an attr for each service used in a test case

    This decorator applies a testtools attr for each service that gets
    exercised by a test case.
    """
    def decorator(f):
        services = ['compute', 'image', 'baremetal', 'volume', 'orchestration',
                    'network', 'identity', 'object_storage', 'dashboard',
                    'telemetry', 'data_processing', 'database']
        for service in args:
            if service not in services:
                raise exceptions.InvalidServiceTag('%s is not a valid '
                                                   'service' % service)
        attr(type=list(args))(f)

        @functools.wraps(f)
        def wrapper(self, *func_args, **func_kwargs):
            service_list = get_service_list()

            for service in args:
                if not service_list[service]:
                    msg = 'Skipped because the %s service is not available' % (
                        service)
                    raise testtools.TestCase.skipException(msg)
            return f(self, *func_args, **func_kwargs)
        return wrapper
    return decorator


def stresstest(**kwargs):
    """Add stress test decorator

    For all functions with this decorator a attr stress will be
    set automatically.

    @param class_setup_per: allowed values are application, process, action
           ``application``: once in the stress job lifetime
           ``process``: once in the worker process lifetime
           ``action``: on each action
    @param allow_inheritance: allows inheritance of this attribute
    """
    def decorator(f):
        if 'class_setup_per' in kwargs:
            setattr(f, "st_class_setup_per", kwargs['class_setup_per'])
        else:
            setattr(f, "st_class_setup_per", 'process')
        if 'allow_inheritance' in kwargs:
            setattr(f, "st_allow_inheritance", kwargs['allow_inheritance'])
        else:
            setattr(f, "st_allow_inheritance", False)
        attr(type='stress')(f)
        return f
    return decorator


def requires_ext(**kwargs):
    """A decorator to skip tests if an extension is not enabled

    @param extension
    @param service
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*func_args, **func_kwargs):
            if not is_extension_enabled(kwargs['extension'],
                                        kwargs['service']):
                msg = "Skipped because %s extension: %s is not enabled" % (
                    kwargs['service'], kwargs['extension'])
                raise testtools.TestCase.skipException(msg)
            return func(*func_args, **func_kwargs)
        return wrapper
    return decorator


def is_extension_enabled(extension_name, service):
    """A function that will check the list of enabled extensions from config

    """
    config_dict = {
        'compute': CONF.compute_feature_enabled.api_extensions,
        'volume': CONF.volume_feature_enabled.api_extensions,
        'network': CONF.network_feature_enabled.api_extensions,
        'object': CONF.object_storage_feature_enabled.discoverable_apis,
        'identity': CONF.identity_feature_enabled.api_extensions
    }
    if len(config_dict[service]) == 0:
        return False
    if config_dict[service][0] == 'all':
        return True
    if extension_name in config_dict[service]:
        return True
    return False


def is_scheduler_filter_enabled(filter_name):
    """Check the list of enabled compute scheduler filters from config. """

    filters = CONF.compute_feature_enabled.scheduler_available_filters
    if len(filters) == 0:
        return False
    if 'all' in filters:
        return True
    if filter_name in filters:
        return True
    return False


at_exit_set = set()


def validate_tearDownClass():
    if at_exit_set:
        LOG.error(
            "tearDownClass does not call the super's "
            "tearDownClass in these classes: \n"
            + str(at_exit_set))


atexit.register(validate_tearDownClass)


class BaseTestCase(testtools.testcase.WithAttributes,
                   testtools.TestCase):
    """The test base class defines Tempest framework for class level fixtures.

    `setUpClass` and `tearDownClass` are defined here and cannot be overwritten
    by subclasses (enforced via hacking rule T105).

    Set-up is split in a series of steps (setup stages), which can be
    overwritten by test classes. Set-up stages are:
    - skip_checks
    - setup_credentials
    - setup_clients
    - resource_setup

    Tear-down is also split in a series of steps (teardown stages), which are
    stacked for execution only if the corresponding setup stage had been
    reached during the setup phase. Tear-down stages are:
    - clear_credentials (defined in the base test class)
    - resource_cleanup
    """

    setUpClassCalled = False
    _service = None

    # NOTE(andreaf) credentials holds a list of the credentials to be allocated
    # at class setup time. Credential types can be 'primary', 'alt', 'admin' or
    # a list of roles - the first element of the list being a label, and the
    # rest the actual roles
    credentials = []
    # Resources required to validate a server using ssh
    validation_resources = {}
    network_resources = {}

    # NOTE(sdague): log_format is defined inline here instead of using the oslo
    # default because going through the config path recouples config to the
    # stress tests too early, and depending on testr order will fail unit tests
    log_format = ('%(asctime)s %(process)d %(levelname)-8s '
                  '[%(name)s] %(message)s')

    # Client manager class to use in this test case.
    client_manager = clients.Manager

    # A way to adjust slow test classes
    TIMEOUT_SCALING_FACTOR = 1

    @classmethod
    def setUpClass(cls):
        # It should never be overridden by descendants
        if hasattr(super(BaseTestCase, cls), 'setUpClass'):
            super(BaseTestCase, cls).setUpClass()
        cls.setUpClassCalled = True
        # Stack of (name, callable) to be invoked in reverse order at teardown
        cls.teardowns = []
        # All the configuration checks that may generate a skip
        cls.skip_checks()
        try:
            # Allocation of all required credentials and client managers
            cls.teardowns.append(('credentials', cls.clear_credentials))
            cls.setup_credentials()
            # Shortcuts to clients
            cls.setup_clients()
            # Additional class-wide test resources
            cls.teardowns.append(('resources', cls.resource_cleanup))
            cls.resource_setup()
        except Exception:
            etype, value, trace = sys.exc_info()
            LOG.info("%s raised in %s.setUpClass. Invoking tearDownClass." % (
                     etype, cls.__name__))
            cls.tearDownClass()
            try:
                six.reraise(etype, value, trace)
            finally:
                del trace  # to avoid circular refs

    @classmethod
    def tearDownClass(cls):
        at_exit_set.discard(cls)
        # It should never be overridden by descendants
        if hasattr(super(BaseTestCase, cls), 'tearDownClass'):
            super(BaseTestCase, cls).tearDownClass()
        # Save any existing exception, we always want to re-raise the original
        # exception only
        etype, value, trace = sys.exc_info()
        # If there was no exception during setup we shall re-raise the first
        # exception in teardown
        re_raise = (etype is None)
        while cls.teardowns:
            name, teardown = cls.teardowns.pop()
            # Catch any exception in tearDown so we can re-raise the original
            # exception at the end
            try:
                teardown()
            except Exception as te:
                sys_exec_info = sys.exc_info()
                tetype = sys_exec_info[0]
                # TODO(andreaf): Till we have the ability to cleanup only
                # resources that were successfully setup in resource_cleanup,
                # log AttributeError as info instead of exception.
                if tetype is AttributeError and name == 'resources':
                    LOG.info("tearDownClass of %s failed: %s" % (name, te))
                else:
                    LOG.exception("teardown of %s failed: %s" % (name, te))
                if not etype:
                    etype, value, trace = sys_exec_info
        # If exceptions were raised during teardown, and not before, re-raise
        # the first one
        if re_raise and etype is not None:
            try:
                six.reraise(etype, value, trace)
            finally:
                del trace  # to avoid circular refs

    @classmethod
    def skip_checks(cls):
        """Class level skip checks.

        Subclasses verify in here all conditions that might prevent the
        execution of the entire test class.
        Checks implemented here may not make use API calls, and should rely on
        configuration alone.
        In general skip checks that require an API call are discouraged.
        If one is really needed it may be implemented either in the
        resource_setup or at test level.
        """
        identity_version = cls.get_identity_version()
        if 'admin' in cls.credentials and not credentials.is_admin_available(
                identity_version=identity_version):
            msg = "Missing Identity Admin API credentials in configuration."
            raise cls.skipException(msg)
        if 'alt' in cls.credentials and not credentials.is_alt_available(
                identity_version=identity_version):
            msg = "Missing a 2nd set of API credentials in configuration."
            raise cls.skipException(msg)
        if hasattr(cls, 'identity_version'):
            if cls.identity_version == 'v2':
                if not CONF.identity_feature_enabled.api_v2:
                    raise cls.skipException("Identity api v2 is not enabled")
            elif cls.identity_version == 'v3':
                if not CONF.identity_feature_enabled.api_v3:
                    raise cls.skipException("Identity api v3 is not enabled")

    @classmethod
    def setup_credentials(cls):
        """Allocate credentials and the client managers from them.

        A test class that requires network resources must override
        setup_credentials and defined the required resources before super
        is invoked.
        """
        for credentials_type in cls.credentials:
            # This may raise an exception in case credentials are not available
            # In that case we want to let the exception through and the test
            # fail accordingly
            if isinstance(credentials_type, six.string_types):
                manager = cls.get_client_manager(
                    credential_type=credentials_type)
                setattr(cls, 'os_%s' % credentials_type, manager)
                # Setup some common aliases
                # TODO(andreaf) The aliases below are a temporary hack
                # to avoid changing too much code in one patch. They should
                # be removed eventually
                if credentials_type == 'primary':
                    cls.os = cls.manager = cls.os_primary
                if credentials_type == 'admin':
                    cls.os_adm = cls.admin_manager = cls.os_admin
                if credentials_type == 'alt':
                    cls.alt_manager = cls.os_alt
            elif isinstance(credentials_type, list):
                manager = cls.get_client_manager(roles=credentials_type[1:],
                                                 force_new=True)
                setattr(cls, 'os_roles_%s' % credentials_type[0], manager)

    @classmethod
    def setup_clients(cls):
        """Create links to the clients into the test object."""
        # TODO(andreaf) There is a fair amount of code that could me moved from
        # base / test classes in here. Ideally tests should be able to only
        # specify which client is `client` and nothing else.
        pass

    @classmethod
    def resource_setup(cls):
        """Class level resource setup for test cases."""
        if hasattr(cls, "os"):
            cls.validation_resources = vresources.create_validation_resources(
                cls.os, cls.validation_resources)
        else:
            LOG.warning("Client manager not found, validation resources not"
                        " created")

    @classmethod
    def resource_cleanup(cls):
        """Class level resource cleanup for test cases.

        Resource cleanup must be able to handle the case of partially setup
        resources, in case a failure during `resource_setup` should happen.
        """
        if cls.validation_resources:
            if hasattr(cls, "os"):
                vresources.clear_validation_resources(cls.os,
                                                      cls.validation_resources)
                cls.validation_resources = {}
            else:
                LOG.warning("Client manager not found, validation resources "
                            "not deleted")

    def setUp(self):
        super(BaseTestCase, self).setUp()
        if not self.setUpClassCalled:
            raise RuntimeError("setUpClass does not calls the super's"
                               "setUpClass in the "
                               + self.__class__.__name__)
        at_exit_set.add(self.__class__)
        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout) * self.TIMEOUT_SCALING_FACTOR
        except ValueError:
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))
        if (os.environ.get('OS_LOG_CAPTURE') != 'False' and
            os.environ.get('OS_LOG_CAPTURE') != '0'):
            self.useFixture(fixtures.LoggerFixture(nuke_handlers=False,
                                                   format=self.log_format,
                                                   level=None))

    @property
    def credentials_provider(self):
        return self._get_credentials_provider()

    @property
    def identity_utils(self):
        """A client that abstracts v2 and v3 identity operations.

        This can be used for creating and tearing down projects in tests. It
        should not be used for testing identity features.
        """
        if CONF.identity.auth_version == 'v2':
            client = self.os_admin.identity_client
            users_client = self.os_admin.users_client
            project_client = self.os_admin.tenants_client
            roles_client = self.os_admin.roles_client
            domains_client = None
        else:
            client = self.os_admin.identity_v3_client
            users_client = self.os_admin.users_v3_client
            project_client = self.os_admin.projects_client
            roles_client = self.os_admin.roles_v3_client
            domains_client = self.os_admin.domains_client

        try:
            domain = client.auth_provider.credentials.project_domain_name
        except AttributeError:
            domain = 'Default'

        return cred_client.get_creds_client(client, project_client,
                                            users_client,
                                            roles_client,
                                            domains_client,
                                            project_domain_name=domain)

    @classmethod
    def get_identity_version(cls):
        """Returns the identity version used by the test class"""
        identity_version = getattr(cls, 'identity_version', None)
        return identity_version or CONF.identity.auth_version

    @classmethod
    def _get_credentials_provider(cls):
        """Returns a credentials provider

        If no credential provider exists yet creates one.
        It uses self.identity_version if defined, or the configuration value
        """
        if (not hasattr(cls, '_creds_provider') or not cls._creds_provider or
                not cls._creds_provider.name == cls.__name__):
            force_tenant_isolation = getattr(cls, 'force_tenant_isolation',
                                             False)

            cls._creds_provider = credentials.get_credentials_provider(
                name=cls.__name__, network_resources=cls.network_resources,
                force_tenant_isolation=force_tenant_isolation,
                identity_version=cls.get_identity_version())
        return cls._creds_provider

    @classmethod
    def get_client_manager(cls, credential_type=None, roles=None,
                           force_new=None):
        """Returns an OpenStack client manager

        Returns an OpenStack client manager based on either credential_type
        or a list of roles. If neither is specified, it defaults to
        credential_type 'primary'
        :param credential_type: string - primary, alt or admin
        :param roles: list of roles

        :returns: the created client manager
        :raises skipException: if the requested credentials are not available
        """
        if all([roles, credential_type]):
            msg = "Cannot get credentials by type and roles at the same time"
            raise ValueError(msg)
        if not any([roles, credential_type]):
            credential_type = 'primary'
        cred_provider = cls._get_credentials_provider()
        if roles:
            for role in roles:
                if not cred_provider.is_role_available(role):
                    skip_msg = (
                        "%s skipped because the configured credential provider"
                        " is not able to provide credentials with the %s role "
                        "assigned." % (cls.__name__, role))
                    raise cls.skipException(skip_msg)
            params = dict(roles=roles)
            if force_new is not None:
                params.update(force_new=force_new)
            creds = cred_provider.get_creds_by_roles(**params)
        else:
            credentials_method = 'get_%s_creds' % credential_type
            if hasattr(cred_provider, credentials_method):
                creds = getattr(cred_provider, credentials_method)()
            else:
                raise exceptions.InvalidCredentials(
                    "Invalid credentials type %s" % credential_type)
        return cls.client_manager(credentials=creds, service=cls._service)

    @classmethod
    def clear_credentials(cls):
        """Clears creds if set"""
        if hasattr(cls, '_creds_provider'):
            cls._creds_provider.clear_creds()

    @classmethod
    def set_validation_resources(cls, keypair=None, floating_ip=None,
                                 security_group=None,
                                 security_group_rules=None):
        """Specify which ssh server validation resources should be created.

        Each of the argument must be set to either None, True or False, with
        None - use default from config (security groups and security group
               rules get created when set to None)
        False - Do not create the validation resource
        True - create the validation resource

        @param keypair
        @param security_group
        @param security_group_rules
        @param floating_ip
        """
        if not CONF.validation.run_validation:
            return
        if keypair is None:
            if CONF.validation.auth_method.lower() == "keypair":
                keypair = True
            else:
                keypair = False
        if floating_ip is None:
            if CONF.validation.connect_method.lower() == "floating":
                floating_ip = True
            else:
                floating_ip = False
        if security_group is None:
            security_group = CONF.validation.security_group
        if security_group_rules is None:
            security_group_rules = CONF.validation.security_group_rules

        if not cls.validation_resources:
            cls.validation_resources = {
                'keypair': keypair,
                'security_group': security_group,
                'security_group_rules': security_group_rules,
                'floating_ip': floating_ip}

    @classmethod
    def set_network_resources(cls, network=False, router=False, subnet=False,
                              dhcp=False):
        """Specify which network resources should be created

        @param network
        @param router
        @param subnet
        @param dhcp
        """
        # network resources should be set only once from callers
        # in order to ensure that even if it's called multiple times in
        # a chain of overloaded methods, the attribute is set only
        # in the leaf class
        if not cls.network_resources:
            cls.network_resources = {
                'network': network,
                'router': router,
                'subnet': subnet,
                'dhcp': dhcp}

    @classmethod
    def get_tenant_network(cls, credentials_type='primary'):
        """Get the network to be used in testing

        :param credentials_type: The type of credentials for which to get the
                                 tenant network

        :return: network dict including 'id' and 'name'
        """
        # Get a manager for the given credentials_type, but at least
        # always fall back on getting the manager for primary credentials
        if isinstance(credentials_type, six.string_types):
            manager = cls.get_client_manager(credential_type=credentials_type)
        elif isinstance(credentials_type, list):
            manager = cls.get_client_manager(roles=credentials_type[1:])
        else:
            manager = cls.get_client_manager()

        # Make sure cred_provider exists and get a network client
        networks_client = manager.compute_networks_client
        cred_provider = cls._get_credentials_provider()
        # In case of nova network, isolated tenants are not able to list the
        # network configured in fixed_network_name, even if they can use it
        # for their servers, so using an admin network client to validate
        # the network name
        if (not CONF.service_available.neutron and
                credentials.is_admin_available(
                    identity_version=cls.get_identity_version())):
            admin_creds = cred_provider.get_admin_creds()
            admin_manager = clients.Manager(admin_creds)
            networks_client = admin_manager.compute_networks_client
        return fixed_network.get_tenant_network(
            cred_provider, networks_client, CONF.compute.fixed_network_name)

    def assertEmpty(self, list, msg=None):
        self.assertTrue(len(list) == 0, msg)

    def assertNotEmpty(self, list, msg=None):
        self.assertTrue(len(list) > 0, msg)


class NegativeAutoTest(BaseTestCase):

    _resources = {}

    @classmethod
    def setUpClass(cls):
        super(NegativeAutoTest, cls).setUpClass()
        os = cls.get_client_manager(credential_type='primary')
        cls.client = os.negative_client

    @staticmethod
    def load_tests(*args):
        """Wrapper for testscenarios

        To set the mandatory scenarios variable only in case a real test
        loader is in place. Will be automatically called in case the variable
        "load_tests" is set.
        """
        if getattr(args[0], 'suiteClass', None) is not None:
            loader, standard_tests, pattern = args
        else:
            standard_tests, module, loader = args
        for test in testtools.iterate_tests(standard_tests):
            schema = getattr(test, '_schema', None)
            if schema is not None:
                setattr(test, 'scenarios',
                        NegativeAutoTest.generate_scenario(schema))
        return testscenarios.load_tests_apply_scenarios(*args)

    @staticmethod
    def generate_scenario(description):
        """Generates the test scenario list for a given description.

        :param description: A file or dictionary with the following entries:
            name (required) name for the api
            http-method (required) one of HEAD,GET,PUT,POST,PATCH,DELETE
            url (required) the url to be appended to the catalog url with '%s'
                for each resource mentioned
            resources: (optional) A list of resource names such as "server",
                "flavor", etc. with an element for each '%s' in the url. This
                method will call self.get_resource for each element when
                constructing the positive test case template so negative
                subclasses are expected to return valid resource ids when
                appropriate.
            json-schema (optional) A valid json schema that will be used to
                create invalid data for the api calls. For "GET" and "HEAD",
                the data is used to generate query strings appended to the url,
                otherwise for the body of the http call.
        """
        LOG.debug(description)
        generator = importutils.import_class(
            CONF.negative.test_generator)()
        generator.validate_schema(description)
        schema = description.get("json-schema", None)
        resources = description.get("resources", [])
        scenario_list = []
        expected_result = None
        for resource in resources:
            if isinstance(resource, dict):
                expected_result = resource['expected_result']
                resource = resource['name']
            LOG.debug("Add resource to test %s" % resource)
            scn_name = "inv_res_%s" % (resource)
            scenario_list.append((scn_name, {
                "resource": (resource, data_utils.rand_uuid()),
                "expected_result": expected_result
            }))
        if schema is not None:
            for scenario in generator.generate_scenarios(schema):
                scenario_list.append((scenario['_negtest_name'],
                                      scenario))
        LOG.debug(scenario_list)
        return scenario_list

    def execute(self, description):
        """Execute a http call

        Execute a http call on an api that are expected to
        result in client errors. First it uses invalid resources that are part
        of the url, and then invalid data for queries and http request bodies.

        :param description: A json file or dictionary with the following
        entries:
            name (required) name for the api
            http-method (required) one of HEAD,GET,PUT,POST,PATCH,DELETE
            url (required) the url to be appended to the catalog url with '%s'
                for each resource mentioned
            resources: (optional) A list of resource names such as "server",
                "flavor", etc. with an element for each '%s' in the url. This
                method will call self.get_resource for each element when
                constructing the positive test case template so negative
                subclasses are expected to return valid resource ids when
                appropriate.
            json-schema (optional) A valid json schema that will be used to
                create invalid data for the api calls. For "GET" and "HEAD",
                the data is used to generate query strings appended to the url,
                otherwise for the body of the http call.

        """
        LOG.info("Executing %s" % description["name"])
        LOG.debug(description)
        generator = importutils.import_class(
            CONF.negative.test_generator)()
        schema = description.get("json-schema", None)
        method = description["http-method"]
        url = description["url"]
        expected_result = None
        if "default_result_code" in description:
            expected_result = description["default_result_code"]

        resources = [self.get_resource(r) for
                     r in description.get("resources", [])]

        if hasattr(self, "resource"):
            # Note(mkoderer): The resources list already contains an invalid
            # entry (see get_resource).
            # We just send a valid json-schema with it
            valid_schema = None
            if schema:
                valid_schema = \
                    valid.ValidTestGenerator().generate_valid(schema)
            new_url, body = self._http_arguments(valid_schema, url, method)
        elif hasattr(self, "_negtest_name"):
            schema_under_test = \
                valid.ValidTestGenerator().generate_valid(schema)
            local_expected_result = \
                generator.generate_payload(self, schema_under_test)
            if local_expected_result is not None:
                expected_result = local_expected_result
            new_url, body = \
                self._http_arguments(schema_under_test, url, method)
        else:
            raise Exception("testscenarios are not active. Please make sure "
                            "that your test runner supports the load_tests "
                            "mechanism")

        if "admin_client" in description and description["admin_client"]:
            if not credentials.is_admin_available(
                    identity_version=self.get_identity_version()):
                msg = ("Missing Identity Admin API credentials in"
                       "configuration.")
                raise self.skipException(msg)
            creds = self.credentials_provider.get_admin_creds()
            os_adm = clients.Manager(credentials=creds)
            client = os_adm.negative_client
        else:
            client = self.client
        resp, resp_body = client.send_request(method, new_url,
                                              resources, body=body)
        self._check_negative_response(expected_result, resp.status, resp_body)

    def _http_arguments(self, json_dict, url, method):
        LOG.debug("dict: %s url: %s method: %s" % (json_dict, url, method))
        if not json_dict:
            return url, None
        elif method in ["GET", "HEAD", "PUT", "DELETE"]:
            return "%s?%s" % (url, urllib.parse.urlencode(json_dict)), None
        else:
            return url, json.dumps(json_dict)

    def _check_negative_response(self, expected_result, result, body):
        self.assertTrue(result >= 400 and result < 500 and result != 413,
                        "Expected client error, got %s:%s" %
                        (result, body))
        self.assertTrue(expected_result is None or expected_result == result,
                        "Expected %s, got %s:%s" %
                        (expected_result, result, body))

    @classmethod
    def set_resource(cls, name, resource):
        """Register a resource for a test

        This function can be used in setUpClass context to register a resource
        for a test.

        :param name: The name of the kind of resource such as "flavor", "role",
            etc.
        :resource: The id of the resource
        """
        cls._resources[name] = resource

    def get_resource(self, name):
        """Return a valid uuid for a type of resource.

        If a real resource is needed as part of a url then this method should
        return one. Otherwise it can return None.

        :param name: The name of the kind of resource such as "flavor", "role",
            etc.
        """
        if isinstance(name, dict):
            name = name['name']
        if hasattr(self, "resource") and self.resource[0] == name:
            LOG.debug("Return invalid resource (%s) value: %s" %
                      (self.resource[0], self.resource[1]))
            return self.resource[1]
        if name in self._resources:
            return self._resources[name]
        return None


def SimpleNegativeAutoTest(klass):
    """This decorator registers a test function on basis of the class name."""
    @attr(type=['negative'])
    def generic_test(self):
        if hasattr(self, '_schema'):
            self.execute(self._schema)

    cn = klass.__name__
    cn = cn.replace('JSON', '')
    cn = cn.replace('Test', '')
    # NOTE(mkoderer): replaces uppercase chars inside the class name with '_'
    lower_cn = re.sub('(?<!^)(?=[A-Z])', '_', cn).lower()
    func_name = 'test_%s' % lower_cn
    setattr(klass, func_name, generic_test)
    return klass


def call_until_true(func, duration, sleep_for):
    """Call the given function until it returns True (and return True)

    or until the specified duration (in seconds) elapses (and return False).

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
        time.sleep(sleep_for)
        now = time.time()
    return False
