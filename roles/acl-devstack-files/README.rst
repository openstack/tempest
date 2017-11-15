Grant global read access to devstack `files` folder.

This is handy to grant the `tempest` user access to VM images for testing.

**Role Variables**

.. zuul:rolevar:: devstack_data_dir
   :default: /opt/stack/data

   The devstack data directory.
