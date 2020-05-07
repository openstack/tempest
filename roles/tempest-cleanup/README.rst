Tempest cleanup
===============

Documentation regarding tempest cleanup can be found at the following
link:
https://docs.openstack.org/tempest/latest/cleanup.html

When init_saved_state and dry_run variables are set to false, the role
execution will run tempest cleanup which deletes resources not present in the
saved_state.json file.

**Role Variables**

.. zuul:rolevar:: devstack_base_dir
   :default: /opt/stack

   The devstack base directory.

.. zuul:rolevar:: init_saved_state
   :default: false

   When true, tempest cleanup --init-saved-state will be executed which
   initializes the saved state of the OpenStack deployment and will output
   a saved_state.json file containing resources from the deployment that will
   be preserved from the cleanup command. This should be done prior to running
   Tempest tests.

.. zuul:rolevar:: dry_run
   :default: false

   When true, tempest cleanup creates a report (./dry_run.json) of the
   resources that would be cleaned up if the role was ran with dry_run option
   set to false.
