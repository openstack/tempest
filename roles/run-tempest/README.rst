Run Tempest

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
   ('all', 'all-plugin'.)

.. zuul:rolevar:: tox_venvlist
   :default: smoke

   The Tempest tox environment to run.
