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

.. zuul:rolevar:: run_tempest_fail_if_leaked_resources
   :default: false

   When true, the role will fail if any leaked resources are detected.
   The detection is done via dry_run.json file which if contains any resources,
   some must have been leaked. This can be also used to verify that tempest
   cleanup was successful.


Role usage
----------

The role can be also used for verification that tempest tests don't leak any
resources or to test that 'tempest cleanup' command deleted all leaked
resources as expected.
Either way the role needs to be run first with init_saved_state variable set
to true prior any tempest tests got executed.
Then, after tempest tests got executed this role needs to be run again with
role variables set according to the desired outcome:

1. to verify that tempest tests don't leak any resources
   run_tempest_dry_cleanup and run_tempest_fail_if_leaked_resources have to
   be set to true.

2. to check that 'tempest cleanup' command deleted all the leaked resources
   run_tempest_cleanup and run_tempest_fail_if_leaked_resources have to be set
   to true.
