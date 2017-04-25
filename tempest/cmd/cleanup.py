#!/usr/bin/env python
#
# Copyright 2014 Dell Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Utility for cleaning up environment after Tempest test run

**Usage:** ``tempest cleanup [--help] [OPTIONS]``

If run with no arguments, ``tempest cleanup`` will query your OpenStack
deployment and build a list of resources to delete and destroy them. This list
will exclude the resources from ``saved_state.json`` and will include the
configured admin account if the ``--delete-tempest-conf-objects`` flag is
specified. By default the admin project is not deleted and the admin user
specified in ``tempest.conf`` is never deleted.

Example Run
-----------

**WARNING: If step 1 is skipped in the example below, the cleanup procedure
may delete resources that existed in the cloud before the test run. This
may cause an unwanted destruction of cloud resources, so use caution with
this command.**

``$ tempest cleanup --init-saved-state``

``$ # Actual running of Tempest tests``

``$ tempest cleanup``

Runtime Arguments
-----------------

**--init-saved-state**: Initializes the saved state of the OpenStack deployment
and will output a ``saved_state.json`` file containing resources from your
deployment that will be preserved from the cleanup command. This should be
done prior to running Tempest tests.

**--delete-tempest-conf-objects**: If option is present, then the command will
delete the admin project in addition to the resources associated with them on
clean up. If option is not present, the command will delete the resources
associated with the Tempest and alternate Tempest users and projects but will
not delete the projects themselves.

**--dry-run**: Creates a report (``./dry_run.json``) of the projects that will
be cleaned up (in the ``_tenants_to_clean`` dictionary [1]_) and the global
objects that will be removed (domains, flavors, images, roles, projects,
and users). Once the cleanup command is executed (e.g. run without
parameters), running it again with **--dry-run** should yield an empty report.

**--help**: Print the help text for the command and parameters.

.. [1] The ``_tenants_to_clean`` dictionary in ``dry_run.json`` lists the
    projects that ``tempest cleanup`` will loop through to delete child
    objects, but the command will, by default, not delete the projects
    themselves. This may differ from the ``tenants`` list as you can clean
    the Tempest and alternate Tempest users and projects but they will not be
    deleted unless the **--delete-tempest-conf-objects** flag is used to
    force their deletion.

"""
import sys
import traceback

from cliff import command
from oslo_log import log as logging
from oslo_serialization import jsonutils as json

from tempest import clients
from tempest.cmd import cleanup_service
from tempest.common import credentials_factory as credentials
from tempest.common import identity
from tempest import config

SAVED_STATE_JSON = "saved_state.json"
DRY_RUN_JSON = "dry_run.json"
LOG = logging.getLogger(__name__)
CONF = config.CONF


class TempestCleanup(command.Command):

    def take_action(self, parsed_args):
        try:
            self.init(parsed_args)
            if not parsed_args.init_saved_state:
                self._cleanup()
        except Exception:
            LOG.exception("Failure during cleanup")
            traceback.print_exc()
            raise

    def init(self, parsed_args):
        cleanup_service.init_conf()
        self.options = parsed_args
        self.admin_mgr = credentials.AdminManager()
        self.dry_run_data = {}
        self.json_data = {}

        self.admin_id = ""
        self.admin_role_id = ""
        self.admin_tenant_id = ""
        self._init_admin_ids()

        self.admin_role_added = []

        # available services
        self.tenant_services = cleanup_service.get_tenant_cleanup_services()
        self.global_services = cleanup_service.get_global_cleanup_services()

        if parsed_args.init_saved_state:
            self._init_state()
            return

        self._load_json()

    def _cleanup(self):
        print("Begin cleanup")
        is_dry_run = self.options.dry_run
        is_preserve = not self.options.delete_tempest_conf_objects
        is_save_state = False

        if is_dry_run:
            self.dry_run_data["_tenants_to_clean"] = {}

        admin_mgr = self.admin_mgr
        # Always cleanup tempest and alt tempest tenants unless
        # they are in saved state json. Therefore is_preserve is False
        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'is_preserve': False,
                  'is_save_state': is_save_state}
        tenant_service = cleanup_service.TenantService(admin_mgr, **kwargs)
        tenants = tenant_service.list()
        print("Process %s tenants" % len(tenants))

        # Loop through list of tenants and clean them up.
        for tenant in tenants:
            self._add_admin(tenant['id'])
            self._clean_tenant(tenant)

        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'is_preserve': is_preserve,
                  'is_save_state': is_save_state}
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        if is_dry_run:
            with open(DRY_RUN_JSON, 'w+') as f:
                f.write(json.dumps(self.dry_run_data, sort_keys=True,
                                   indent=2, separators=(',', ': ')))

        self._remove_admin_user_roles()

    def _remove_admin_user_roles(self):
        tenant_ids = self.admin_role_added
        LOG.debug("Removing admin user roles where needed for tenants: %s",
                  tenant_ids)
        for tenant_id in tenant_ids:
            self._remove_admin_role(tenant_id)

    def _clean_tenant(self, tenant):
        print("Cleaning tenant:  %s " % tenant['name'])
        is_dry_run = self.options.dry_run
        dry_run_data = self.dry_run_data
        is_preserve = not self.options.delete_tempest_conf_objects
        tenant_id = tenant['id']
        tenant_name = tenant['name']
        tenant_data = None
        if is_dry_run:
            tenant_data = dry_run_data["_tenants_to_clean"][tenant_id] = {}
            tenant_data['name'] = tenant_name

        kwargs = {"username": CONF.auth.admin_username,
                  "password": CONF.auth.admin_password,
                  "tenant_name": tenant['name']}
        mgr = clients.Manager(credentials=credentials.get_credentials(
            **kwargs))
        kwargs = {'data': tenant_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': None,
                  'is_preserve': is_preserve,
                  'is_save_state': False,
                  'tenant_id': tenant_id}
        for service in self.tenant_services:
            svc = service(mgr, **kwargs)
            svc.run()

    def _init_admin_ids(self):
        tn_cl = self.admin_mgr.tenants_client
        rl_cl = self.admin_mgr.roles_client

        tenant = identity.get_tenant_by_name(tn_cl,
                                             CONF.auth.admin_project_name)
        self.admin_tenant_id = tenant['id']

        user = identity.get_user_by_username(tn_cl, self.admin_tenant_id,
                                             CONF.auth.admin_username)
        self.admin_id = user['id']

        roles = rl_cl.list_roles()['roles']
        for role in roles:
            if role['name'] == CONF.identity.admin_role:
                self.admin_role_id = role['id']
                break

    def get_parser(self, prog_name):
        parser = super(TempestCleanup, self).get_parser(prog_name)
        parser.add_argument('--init-saved-state', action="store_true",
                            dest='init_saved_state', default=False,
                            help="Creates JSON file: " + SAVED_STATE_JSON +
                            ", representing the current state of your "
                            "deployment,  specifically object types "
                            "tempest creates and destroys during a run. "
                            "You must run with this flag prior to "
                            "executing cleanup in normal mode, which is with "
                            "no arguments.")
        parser.add_argument('--delete-tempest-conf-objects',
                            action="store_true",
                            dest='delete_tempest_conf_objects',
                            default=False,
                            help="Force deletion of the tempest and "
                            "alternate tempest users and tenants.")
        parser.add_argument('--dry-run', action="store_true",
                            dest='dry_run', default=False,
                            help="Generate JSON file:" + DRY_RUN_JSON +
                            ", that reports the objects that would have "
                            "been deleted had a full cleanup been run.")
        return parser

    def get_description(self):
        return 'Cleanup after tempest run'

    def _add_admin(self, tenant_id):
        rl_cl = self.admin_mgr.roles_client
        needs_role = True
        roles = rl_cl.list_user_roles_on_project(tenant_id,
                                                 self.admin_id)['roles']
        for role in roles:
            if role['id'] == self.admin_role_id:
                needs_role = False
                LOG.debug("User already had admin privilege for this tenant")
        if needs_role:
            LOG.debug("Adding admin privilege for : %s", tenant_id)
            rl_cl.create_user_role_on_project(tenant_id, self.admin_id,
                                              self.admin_role_id)
            self.admin_role_added.append(tenant_id)

    def _remove_admin_role(self, tenant_id):
        LOG.debug("Remove admin user role for tenant: %s", tenant_id)
        # Must initialize AdminManager for each user role
        # Otherwise authentication exception is thrown, weird
        id_cl = credentials.AdminManager().identity_client
        if (self._tenant_exists(tenant_id)):
            try:
                id_cl.delete_role_from_user_on_project(tenant_id,
                                                       self.admin_id,
                                                       self.admin_role_id)
            except Exception as ex:
                LOG.exception("Failed removing role from tenant which still"
                              "exists, exception: %s", ex)

    def _tenant_exists(self, tenant_id):
        tn_cl = self.admin_mgr.tenants_client
        try:
            t = tn_cl.show_tenant(tenant_id)
            LOG.debug("Tenant is: %s", str(t))
            return True
        except Exception as ex:
            LOG.debug("Tenant no longer exists? %s", ex)
            return False

    def _init_state(self):
        print("Initializing saved state.")
        data = {}
        admin_mgr = self.admin_mgr
        kwargs = {'data': data,
                  'is_dry_run': False,
                  'saved_state_json': data,
                  'is_preserve': False,
                  'is_save_state': True}
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        with open(SAVED_STATE_JSON, 'w+') as f:
            f.write(json.dumps(data,
                    sort_keys=True, indent=2, separators=(',', ': ')))

    def _load_json(self):
        try:
            with open(SAVED_STATE_JSON) as json_file:
                self.json_data = json.load(json_file)

        except IOError as ex:
            LOG.exception("Failed loading saved state, please be sure you"
                          " have first run cleanup with --init-saved-state "
                          "flag prior to running tempest. Exception: %s", ex)
            sys.exit(ex)
        except Exception as ex:
            LOG.exception("Exception parsing saved state json : %s", ex)
            sys.exit(ex)
