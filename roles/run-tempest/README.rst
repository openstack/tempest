Run Tempest

The result of the tempest run is stored in the `tempest_run_result`
variable (through the `register` statement).

**Role Variables**

.. zuul:rolevar:: devstack_base_dir
   :default: /opt/stack

   The devstack base directory.

.. zuul:rolevar:: tempest_concurrency
   :default: 0

   The number of parallel test processes.

.. zuul:rolevar:: tempest_test_regex
   :default: ''

   A regular expression used to select the tests.

   It works only when used with some specific tox environments
   ('all', 'all-site-packages').

   In the following example only api scenario and third party tests
   will be executed.

       ::
           vars:
             tempest_test_regex: (tempest\.(api|scenario|thirdparty)).*$

.. zuul:rolevar:: tempest_test_blacklist

   DEPRECATED option, please use tempest_test_exclude_list instead.

.. zuul:rolevar:: tempest_test_exclude_list

   Specifies an excludelist file to skip tests that are not needed.

   Pass a full path to the file.

.. zuul:rolevar:: tox_envlist
   :default: smoke

   The Tempest tox environment to run.

.. zuul:rolevar:: tempest_black_regex
   :default: ''

   DEPRECATED option, please use tempest_exclude_regex instead.

.. zuul:rolevar:: tempest_exclude_regex
   :default: ''

   A regular expression used to skip the tests.

   It works only when used with some specific tox environments
   ('all', 'all-site-packages').

       ::
           vars:
             tempest_exclude_regex: (tempest.api.identity).*$

.. zuul:rolevar:: tox_extra_args
   :default: ''

   String of extra command line options to pass to tox.

   Here is an example of running tox with --sitepackages option:

       ::
           vars:
             tox_extra_args: --sitepackages

.. zuul:rolevar:: tempest_test_timeout
   :default: ''

   The timeout (in seconds) for each test.

.. zuul:rolevar:: stable_constraints_file
   :default: ''

   Upper constraints file to be used for stable branch till stable/victoria.

.. zuul:rolevar:: tempest_tox_environment
   :default: ''

   Environment variable to set for run-tempst task.

   Env variables set in this variable will be combined with some more
   defaults env variable set at runtime.
