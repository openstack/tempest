Tempest Field Guide to Exceptions
=================================


What are these exceptions?
--------------------------

These exceptions are used by Tempest for covering OpenStack specific exceptional
cases.

How to add new exceptions?
--------------------------

Each exception-template for inheritance purposes should be added into 'base'
submodule.
All other exceptions can be added in two ways:
- in main module
- in submodule
But only in one of the ways. Need to make sure, that new exception is not
present already.

How to use exceptions?
----------------------

Any exceptions from this module or its submodules should be used in appropriate
places to handle exceptional cases.
Classes from 'base' module should be used only for inheritance.
