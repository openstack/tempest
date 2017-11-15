Setup the `tempest` user as owner of Tempest's data folder.

Tempest's devstack plugin creates the data folder, but it has no knowledge
of the `tempest` user, so we need a role to fix ownership on the data folder.


**Role Variables**

.. zuul:rolevar:: devstack_data_dir
   :default: /opt/stack/data

   The devstack data directory.
