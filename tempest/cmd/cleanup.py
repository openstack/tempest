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

    We advice not to run tempest cleanup on production environments.

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
  should be done prior to running Tempest tests. Note, that if other users of
  your cloud could have created resources after running ``--init-saved-state``,
  it would not protect those resources as they wouldn't be present in the
  saved_state.json file.

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
  report. We STRONGLY ENCOURAGE to run ``tempest cleanup`` with ``--dry-run``
  first and then verify that the resources listed in the ``dry_run.json`` file
  are meant to be deleted.

* ``--prefix``: Only resources that match the prefix will be deleted. When this
  option is used, ``saved_state.json`` file is not needed (no need to run with
  ``--init-saved-state`` first).

  All tempest resources are created with the prefix value from the config
  option ``resource_name_prefix`` in tempest.conf. To cleanup only the
  resources created by tempest, you should use the prefix set in your
  tempest.conf (the default value of ``resource_name_prefix`` is ``tempest``.

  Note, that some resources are not named thus they will not be deleted when
  filtering based on the prefix. This option will be ignored when
  ``--init-saved-state`` is used so that it can capture the true init state -
  all resources present at that moment. If there is any ``saved_state.json``
  file present (e.g. if you ran the tempest cleanup with ``--init-saved-state``
  before) and you run the tempest cleanup with ``--prefix``, the
  ``saved_state.json`` file will be ignored and cleanup will be done based on
  the passed prefix only.

* ``--resource-list``: Allows the use of file ``./resource_list.json``, which
  contains all resources created by Tempest during all Tempest runs, to
  create another method for removing only resources created by Tempest.
  List of these resources is created when config option ``record_resources``
  in default section is set to true. After using this option for cleanup,
  the existing ``./resource_list.json`` is cleared from deleted resources.

  When this option is used, ``saved_state.json`` file is not needed (no
  need to run with ``--init-saved-state`` first). If there is any
  ``saved_state.json`` file present and you run the tempest cleanup with
  ``--resource-list``, the ``saved_state.json`` file will be ignored and
  cleanup will be done based on the ``resource_list.json`` only.

  If you run tempest cleanup with both ``--prefix`` and ``--resource-list``,
  the ``--resource-list`` option will be ignored and cleanup will be done
  based on the ``--prefix`` option only.

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
from tempest import config
from tempest.lib import exceptions

SAVED_STATE_JSON = "saved_state.json"
DRY_RUN_JSON = "dry_run.json"
RESOURCE_LIST_JSON = "resource_list.json"
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
        # set new handler for logging to stdout, by default only INFO messages
        # are logged to stdout
        stdout_handler = logging.logging.StreamHandler()
        # debug argument is defined in cliff already
        if self.app_args.debug:
            stdout_handler.level = logging.DEBUG
        else:
            stdout_handler.level = logging.INFO
        LOG.handlers.append(stdout_handler)

        cleanup_service.init_conf()
        self.options = parsed_args
        self.admin_mgr = clients.Manager(
            credentials.get_configured_admin_credentials())
        self.dry_run_data = {}
        self.resource_data = {}
        self.json_data = {}

        # available services
        self.project_associated_services = (
            cleanup_service.get_project_associated_cleanup_services())
        self.resource_cleanup_services = (
            cleanup_service.get_resource_cleanup_services())
        self.global_services = cleanup_service.get_global_cleanup_services()

        if parsed_args.init_saved_state:
            self._init_state()
            return

        if parsed_args.prefix:
            return

        if parsed_args.resource_list:
            self._load_resource_list()
            return

        self._load_saved_state()

    def _cleanup(self):
        LOG.info("Begin cleanup")
        is_dry_run = self.options.dry_run
        is_preserve = not self.options.delete_tempest_conf_objects
        is_resource_list = self.options.resource_list
        is_save_state = False
        cleanup_prefix = self.options.prefix

        if is_dry_run:
            self.dry_run_data["_projects_to_clean"] = {}

        admin_mgr = self.admin_mgr
        # Always cleanup tempest and alt tempest projects unless
        # they are in saved state json. Therefore is_preserve is False
        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'resource_list_json': self.resource_data,
                  'saved_state_json': self.json_data,
                  'is_preserve': False,
                  'is_resource_list': is_resource_list,
                  'is_save_state': is_save_state,
                  'prefix': cleanup_prefix}
        project_service = cleanup_service.ProjectService(admin_mgr, **kwargs)
        projects = project_service.list()
        LOG.info("Processing %s projects", len(projects))

        # Loop through list of projects and clean them up.
        for project in projects:
            self._clean_project(project)

        kwargs = {'data': self.dry_run_data,
                  'is_dry_run': is_dry_run,
                  'resource_list_json': self.resource_data,
                  'saved_state_json': self.json_data,
                  'is_preserve': is_preserve,
                  'is_resource_list': is_resource_list,
                  'is_save_state': is_save_state,
                  'prefix': cleanup_prefix,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        LOG.info("Processing global services")
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        LOG.info("Processing services")
        for service in self.resource_cleanup_services:
            svc = service(self.admin_mgr, **kwargs)
            svc.run()

        if is_dry_run:
            with open(DRY_RUN_JSON, 'w+') as f:
                f.write(json.dumps(self.dry_run_data, sort_keys=True,
                                   indent=2, separators=(',', ': ')))

        if is_resource_list:
            LOG.info("Clearing 'resource_list.json' file.")
            with open(RESOURCE_LIST_JSON, 'w') as f:
                f.write('{}')

    def _clean_project(self, project):
        LOG.debug("Cleaning project:  %s ", project['name'])
        is_dry_run = self.options.dry_run
        dry_run_data = self.dry_run_data
        is_preserve = not self.options.delete_tempest_conf_objects
        is_resource_list = self.options.resource_list
        project_id = project['id']
        project_name = project['name']
        project_data = None
        cleanup_prefix = self.options.prefix
        if is_dry_run:
            project_data = dry_run_data["_projects_to_clean"][project_id] = {}
            project_data['name'] = project_name

        kwargs = {'data': project_data,
                  'is_dry_run': is_dry_run,
                  'saved_state_json': self.json_data,
                  'resource_list_json': self.resource_data,
                  'is_preserve': is_preserve,
                  'is_resource_list': is_resource_list,
                  'is_save_state': False,
                  'project_id': project_id,
                  'prefix': cleanup_prefix,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        for service in self.project_associated_services:
            svc = service(self.admin_mgr, **kwargs)
            svc.run()

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
        parser.add_argument('--prefix', dest='prefix', default=None,
                            help="Only resources that match the prefix will "
                            "be deleted (resources in saved_state.json are "
                            "not taken into account). All tempest resources "
                            "are created with the prefix value set by "
                            "resource_name_prefix in tempest.conf, default "
                            "prefix is tempest. Note that some resources are "
                            "not named thus they will not be deleted when "
                            "filtering based on the prefix. This opt will be "
                            "ignored when --init-saved-state is used so that "
                            "it can capture the true init state - all "
                            "resources present at that moment.")
        parser.add_argument('--resource-list', action="store_true",
                            dest='resource_list', default=False,
                            help="Runs tempest cleanup with generated "
                            "JSON file: " + RESOURCE_LIST_JSON + " to "
                            "erase resources created during Tempest run. "
                            "NOTE: To create " + RESOURCE_LIST_JSON + " "
                            "set config option record_resources under default "
                            "section in tempest.conf file to true. This "
                            "option will be ignored when --init-saved-state "
                            "is used so that it can capture the true init "
                            "state - all resources present at that moment. "
                            "This option will be ignored if passed with "
                            "--prefix.")
        return parser

    def get_description(self):
        return ('tempest cleanup tool, read the full documentation before '
                'using this tool. We advice not to run it on production '
                'environments. On environments where also other users may '
                'create resources, we strongly advice using --dry-run '
                'argument first and verify the content of dry_run.json file.')

    def _init_state(self):
        LOG.info("Initializing saved state.")
        data = {}
        admin_mgr = self.admin_mgr
        kwargs = {'data': data,
                  'is_dry_run': False,
                  'saved_state_json': data,
                  'is_preserve': False,
                  'is_resource_list': False,
                  'is_save_state': True,
                  # must be None as we want to capture true init state
                  # (all resources present) thus no filtering based
                  # on the prefix
                  'prefix': None,
                  'got_exceptions': self.GOT_EXCEPTIONS}
        for service in self.global_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        for service in self.project_associated_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        for service in self.resource_cleanup_services:
            svc = service(admin_mgr, **kwargs)
            svc.run()

        with open(SAVED_STATE_JSON, 'w+') as f:
            f.write(json.dumps(data, sort_keys=True,
                               indent=2, separators=(',', ': ')))

    def _load_resource_list(self, resource_list_json=RESOURCE_LIST_JSON):
        try:
            with open(resource_list_json, 'rb') as json_file:
                self.resource_data = json.load(json_file)
        except IOError as ex:
            LOG.exception(
                "Failed loading 'resource_list.json', please "
                "be sure you created this file by setting config "
                "option record_resources in default section to true "
                "prior to running tempest. Exception: %s", ex)
            sys.exit(ex)
        except Exception as ex:
            LOG.exception(
                "Exception parsing 'resource_list.json' : %s", ex)
            sys.exit(ex)

    def _load_saved_state(self, saved_state_json=SAVED_STATE_JSON):
        try:
            with open(saved_state_json, 'rb') as json_file:
                self.json_data = json.load(json_file)
        except IOError as ex:
            LOG.exception(
                "Failed loading saved state, please be sure you"
                " have first run cleanup with --init-saved-state "
                "flag prior to running tempest. Exception: %s", ex)
            sys.exit(ex)
        except Exception as ex:
            LOG.exception("Exception parsing saved state json : %s", ex)
            sys.exit(ex)
