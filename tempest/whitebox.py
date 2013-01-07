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
import os
import shlex
import subprocess
import sys

import nose
from sqlalchemy import create_engine, MetaData

from tempest.common.ssh import Client
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest import test
from tempest.tests import compute

LOG = logging.getLogger(__name__)


class WhiteboxTest(object):

    """
    Base test case class mixin for "whitebox tests"

    Whitebox tests are tests that have the following characteristics:

     * Test common and advanced operations against a set of servers
     * Use a client that it is possible to send random or bad data with
     * SSH into either a host or a guest in order to validate server state
     * May execute SQL queries directly against internal databases to verify
       the state of data records
    """
    pass


class ComputeWhiteboxTest(test.ComputeFuzzClientTest, WhiteboxTest):

    """
    Base smoke test case class for OpenStack Compute API (Nova)
    """

    @classmethod
    def setUpClass(cls):
        if not compute.WHITEBOX_ENABLED:
            msg = "Whitebox testing disabled"
            raise nose.SkipTest(msg)

        super(ComputeWhiteboxTest, cls).setUpClass()

        # Add some convenience attributes that tests use...
        cls.nova_dir = cls.config.compute.source_dir
        cls.compute_bin_dir = cls.config.compute.bin_dir
        cls.compute_config_path = cls.config.compute.config_path
        cls.servers_client = cls.manager.servers_client
        cls.images_client = cls.manager.images_client
        cls.flavors_client = cls.manager.flavors_client
        cls.extensions_client = cls.manager.extensions_client
        cls.floating_ips_client = cls.manager.floating_ips_client
        cls.keypairs_client = cls.manager.keypairs_client
        cls.security_groups_client = cls.manager.security_groups_client
        cls.console_outputs_client = cls.manager.console_outputs_client
        cls.limits_client = cls.manager.limits_client
        cls.volumes_client = cls.manager.volumes_client
        cls.build_interval = cls.config.compute.build_interval
        cls.build_timeout = cls.config.compute.build_timeout
        cls.ssh_user = cls.config.compute.ssh_user
        cls.image_ref = cls.config.compute.image_ref
        cls.image_ref_alt = cls.config.compute.image_ref_alt
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.flavor_ref_alt = cls.config.compute.flavor_ref_alt
        cls.servers = []

    @classmethod
    def tearDownClass(cls):
        # NOTE(jaypipes): Tests often add things in a particular order
        # so we destroy resources in the reverse order in which resources
        # are added to the test class object
        if not cls.resources:
            return
        thing = cls.resources.pop()
        while True:
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))
            # Resources in novaclient all have a delete() method
            # which destroys the resource...
            thing.delete()
            if not cls.resources:
                return
            thing = cls.resources.pop()

    @classmethod
    def create_server(cls, image_id=None):
        """Wrapper utility that returns a test server."""
        server_name = rand_name(cls.__name__ + "-instance")
        flavor = cls.flavor_ref
        if not image_id:
            image_id = cls.image_ref

        resp, server = cls.servers_client.create_server(
                                                server_name, image_id, flavor)
        cls.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        cls.servers.append(server)
        return server

    @classmethod
    def get_db_handle_and_meta(cls, database='nova'):
        """Return a connection handle and metadata of an OpenStack database."""
        engine_args = {"echo": False,
                       "convert_unicode": True,
                       "pool_recycle": 3600
                       }

        try:
            engine = create_engine(cls.config.compute.db_uri, **engine_args)
            connection = engine.connect()
            meta = MetaData()
            meta.reflect(bind=engine)

        except Exception, e:
            raise exceptions.SQLException(message=e)

        return connection, meta

    def nova_manage(self, category, action, params):
        """Executes nova-manage command for the given action."""

        nova_manage_path = os.path.join(self.compute_bin_dir, 'nova-manage')
        cmd = ' '.join([nova_manage_path, category, action, params])

        if self.deploy_mode == 'devstack-local':
            if not os.path.isdir(self.nova_dir):
                sys.exit("Cannot find Nova source directory: %s" %
                         self.nova_dir)

            cmd = shlex.split(cmd)
            result = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        #Todo(rohitk): Need to define host connection parameters in config
        else:
            client = self.get_ssh_connection(self.config.whitebox.api_host,
                                             self.config.whitebox.api_user,
                                             self.config.whitebox.api_passwd)
            result = client.exec_command(cmd)

        return result

    def get_ssh_connection(self, host, username, password):
        """Create an SSH connection object to a host."""
        ssh_timeout = self.config.compute.ssh_timeout
        ssh_client = Client(host, username, password, ssh_timeout)
        if not ssh_client.test_connection_auth():
            raise exceptions.SSHTimeout()
        else:
            return ssh_client
