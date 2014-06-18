Tempest Field Guide to Baremetal API tests
==========================================


What are these tests?
---------------------

These tests stress the OpenStack baremetal provisioning API provided by
Ironic.


Why are these tests in tempest?
------------------------------

The purpose of these tests is to exercise the various APIs provided by Ironic
for managing baremetal nodes.


Scope of these tests
--------------------

The baremetal API test perform basic CRUD operations on the Ironic node
inventory.  They do not actually perform hardware provisioning. It is important
to note that all Ironic API actions are admin operations meant to be used
either by cloud operators or other OpenStack services (i.e., Nova).
