Setup Tempest run folder.

To support isolation between multiple runs, separate run folders are required.
Set `tempest` as owner of Tempest's current run folder.
There is an implicit assumption here of a one to one relationship between
devstack versions and Tempest runs.


**Role Variables**

.. zuul:rolevar:: devstack_base_dir
   :default: /opt/stack

   The devstack base directory.
