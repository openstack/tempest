# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

import functools

import testtools

from tempest import config
from tempest.exceptions import InvalidServiceTag
from tempest.lib import decorators


CONF = config.CONF


def get_service_list():
    service_list = {
        'compute': CONF.service_available.nova,
        'image': CONF.service_available.glance,
        'volume': CONF.service_available.cinder,
        # NOTE(masayukig): We have two network services which are neutron and
        # nova-network. And we have no way to know whether nova-network is
        # available or not. After the pending removal of nova-network from
        # nova, we can treat the network/neutron case in the same manner as
        # the other services.
        'network': True,
        # NOTE(masayukig): Tempest tests always require the identity service.
        # So we should set this True here.
        'identity': True,
        'object_storage': CONF.service_available.swift,
        'dashboard': CONF.service_available.horizon,
    }
    return service_list


def services(*args):
    """A decorator used to set an attr for each service used in a test case

    This decorator applies a testtools attr for each service that gets
    exercised by a test case.
    """
    def decorator(f):
        known_services = get_service_list()

        for service in args:
            if service not in known_services:
                raise InvalidServiceTag('%s is not a valid service' % service)
        decorators.attr(type=list(args))(f)

        @functools.wraps(f)
        def wrapper(*func_args, **func_kwargs):
            service_list = get_service_list()

            for service in args:
                if not service_list[service]:
                    msg = 'Skipped because the %s service is not available' % (
                        service)
                    raise testtools.TestCase.skipException(msg)
            return f(*func_args, **func_kwargs)
        return wrapper
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
    if not config_dict[service]:
        return False
    if config_dict[service][0] == 'all':
        return True
    if extension_name in config_dict[service]:
        return True
    return False


def is_network_feature_enabled(feature_name):
    """A function that will check the list of available network features

    """
    list_of_features = CONF.network_feature_enabled.available_features

    if not list_of_features:
        return False
    if list_of_features[0] == 'all':
        return True
    if feature_name in list_of_features:
        return True
    return False
