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

.. warning::

    If step 1 is skipped in the example below, the cleanup procedure
    may delete resources that existed in the cloud before the test run. This
    may cause an unwanted destruction of cloud resources, so use caution with
    this command.

    Examples::

     $ tempest cleanup --init-saved-state
     $ # Actual running of Tempest tests
     $ tempest cleanup

Runtime Arguments
-----------------

* ``--init-saved-state``: Initializes the saved state of the OpenStack
  deployment and will output a ``saved_state.json`` file containing resources
  from your deployment that will be preserved from the cleanup command. This
  should be done prior to running Tempest tests.

* ``--delete-tempest-conf-objects``: If option is present, then the command
  will delete the admin project in addition to the resources associated with
  them on clean up. If option is not present, the command will delete the
  resources associated with the Tempest and alternate Tempest users and
  projects but will not delete the projects themselves.

* ``--dry-run``: Creates a report (``./dry_run.json``) of the projects that
  will be cleaned up (in the ``_projects_to_clean`` dictionary [1]_) and the
  global objects that will be removed (domains, flavors, images, roles,
  projects, and users). Once the cleanup command is executed (e.g. run without
  parameters), running it again with ``--dry-run`` should yield an empty
  report.

* ``--help``: Print the help text for the command and parameters.

.. [1] The ``_projects_to_clean`` dictionary in ``dry_run.json`` lists the
    projects that ``tempest cleanup`` will loop through to delete child
    objects, but the command will, by default, not delete the projects
    themselves. This may differ from the ``projects`` list as you can clean
    the Tempest and alternate Tempest users and projects but they will not be
    deleted unless the ``--delete-tempest-conf-objects`` flag is used to
    force their deletion.

.. note::

    If during execution of ``tempest cleanup`` NotImplemented exception
    occurres, ``tempest cleanup`` won't fail on that, it will be logged only.
    NotImplemented errors are ignored because they are an outcome of some
    extensions being disabled and ``tempest cleanup`` is not checking their
    availability as it tries to clean up as much as possible without any
    complicated logic.

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
from tempest.lib import exceptions

SAVED_STATE_JSON = "saved_state.json"
DRY_RUN_JSON = "dry_run.json"
LOG = logging.getLogger(__name__)
CONF = config.CONF


class TempestCleanup(command.Command):

    GOT_EXCEPTIONS = []

    def take_action(self, parsed_args):
        try:
            self.init(parsed_args)
            if not parsed_args.init_saved_state:
                self._cleanup()
        except Exception:
            LOG.exception("Failure during cleanup")
            traceback.print_exc()
            raise
        # ignore NotImplemented errors as those are an outcome of some
        # extensions being disabled and cleanup is not checking their
        # availability as it tries to clean up as much as possible without
        # any complicated logic
        critical_exceptions = [ex for ex in self.GOT_EXCEPTIONS if
                               not isinstance(ex, exceptions.NotImplemented)]
        if critical_exceptions:
            raise Exception(self.GOT_EXCEPTIONS)

    def init(self, parsed_args):
        cleanup_service.init_conf()
        self.options = parsed_args
        self.admin_mgr = clients.Manager(
            credentials.get_configured_admin_credentials())
        self.dry_run_data = {}
        self.json_data = {}

        self.admin_id = ""
        self.admin_role_id = ""
        self.admin_project_id = ""
        self._init_admin_ids()

        self.admin_role_added = []

        # available services
        self.project_services = cleanup_service.get_project_cleanup_services()
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
            self.dry_run_data["_projects_to_clean"] = {}

        admin_mgr = self.admin_mgr
        # Always cleanup tempest and alt tempest projects unless
        # they are in saved state json. Therefore is_preserve is False
        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'is_preserve': False,
                  'is_save_state': is_save_state}
        project_service = cleanup_service.ProjectService(admin_mgr, **kwargs)
        projects = project_service.list()
        print("Process %s projects" % len(projects))

        # Loop through list of projects and clean them up.
        for project in projects:
            self._add_admin(project['id'])
            self._clean_project(project)

        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'is_preserve': is_preserve,
                  'is_save_state': is_save_state,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        if is_dry_run:
            with open(DRY_RUN_JSON, 'w+') as f:
                f.write(json.dumps(self.dry_run_data, sort_keys=True,
                                   indent=2, separators=(',', ': ')))

        self._remove_admin_user_roles()

    def _remove_admin_user_roles(self):
        project_ids = self.admin_role_added
        LOG.debug("Removing admin user roles where needed for projects: %s",
                  project_ids)
        for project_id in project_ids:
            self._remove_admin_role(project_id)

    def _clean_project(self, project):
        print("Cleaning project:  %s " % project['name'])
        is_dry_run = self.options.dry_run
        dry_run_data = self.dry_run_data
        is_preserve = not self.options.delete_tempest_conf_objects
        project_id = project['id']
        project_name = project['name']
        project_data = None
        if is_dry_run:
            project_data = dry_run_data["_projects_to_clean"][project_id] = {}
            project_data['name'] = project_name

        kwargs = {"username": CONF.auth.admin_username,
                  "password": CONF.auth.admin_password,
                  "project_name": project['name']}
        mgr = clients.Manager(credentials=credentials.get_credentials(
            **kwargs))
        kwargs = {'data': project_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'is_preserve': is_preserve,
                  'is_save_state': False,
                  'project_id': project_id,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        for service in self.project_services:
            svc = service(mgr, **kwargs)
            svc.run()

    def _init_admin_ids(self):
        pr_cl = self.admin_mgr.projects_client
        rl_cl = self.admin_mgr.roles_v3_client
        rla_cl = self.admin_mgr.role_assignments_client
        us_cl = self.admin_mgr.users_v3_client

        project = identity.get_project_by_name(pr_cl,
                                               CONF.auth.admin_project_name)
        self.admin_project_id = project['id']
        user = identity.get_user_by_project(us_cl, rla_cl,
                                            self.admin_project_id,
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
                            "alternate tempest users and projects.")
        parser.add_argument('--dry-run', action="store_true",
                            dest='dry_run', default=False,
                            help="Generate JSON file:" + DRY_RUN_JSON +
                            ", that reports the objects that would have "
                            "been deleted had a full cleanup been run.")
        return parser

    def get_description(self):
        return 'Cleanup after tempest run'

    def _add_admin(self, project_id):
        rl_cl = self.admin_mgr.roles_v3_client
        needs_role = True
        roles = rl_cl.list_user_roles_on_project(project_id,
                                                 self.admin_id)['roles']
        for role in roles:
            if role['id'] == self.admin_role_id:
                needs_role = False
                LOG.debug("User already had admin privilege for this project")
        if needs_role:
            LOG.debug("Adding admin privilege for : %s", project_id)
            rl_cl.create_user_role_on_project(project_id, self.admin_id,
                                              self.admin_role_id)
            self.admin_role_added.append(project_id)

    def _remove_admin_role(self, project_id):
        LOG.debug("Remove admin user role for projectt: %s", project_id)
        # Must initialize Admin Manager for each user role
        # Otherwise authentication exception is thrown, weird
        id_cl = clients.Manager(
            credentials.get_configured_admin_credentials()).identity_client
        if (self._project_exists(project_id)):
            try:
                id_cl.delete_role_from_user_on_project(project_id,
                                                       self.admin_id,
                                                       self.admin_role_id)
            except Exception as ex:
                LOG.exception("Failed removing role from project which still "
                              "exists, exception: %s", ex)

    def _project_exists(self, project_id):
        pr_cl = self.admin_mgr.projects_client
        try:
            p = pr_cl.show_project(project_id)
            LOG.debug("Project is: %s", str(p))
            return True
        except Exception as ex:
            LOG.debug("Project no longer exists? %s", ex)
            return False

    def _init_state(self):
        print("Initializing saved state.")
        data = {}
        admin_mgr = self.admin_mgr
        kwargs = {'data': data,
                  'is_dry_run': False,
                  'saved_state_json': data,
                  'is_preserve': False,
                  'is_save_state': True,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        for service in self.project_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        with open(SAVED_STATE_JSON, 'w+') as f:
            f.write(json.dumps(data, sort_keys=True,
                               indent=2, separators=(',', ': ')))

    def _load_json(self, saved_state_json=SAVED_STATE_JSON):
        try:
            with open(saved_state_json, 'rb') as json_file:
                self.json_data = json.load(json_file)

        except IOError as ex:
            LOG.exception("Failed loading saved state, please be sure you"
                          " have first run cleanup with --init-saved-state "
                          "flag prior to running tempest. Exception: %s", ex)
            sys.exit(ex)
        except Exception as ex:
            LOG.exception("Exception parsing saved state json : %s", ex)
            sys.exit(ex)
