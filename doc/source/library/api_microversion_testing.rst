.. _api_microversion_testing:

API Microversion Testing Support in Tempest
===========================================

---------------------------------------------
Framework to support API Microversion testing
---------------------------------------------

Many of the OpenStack components have implemented API microversions.
It is important to test those microversions in Tempest or external plugins.
Tempest now provides stable interfaces to support testing the API microversions.
Based on the microversion range coming from the combination of both configuration
and each test case, APIs requests will be made with the selected microversion.

This document explains the interfaces needed for microversion testing.


The api_version_request module
""""""""""""""""""""""""""""""

.. automodule:: tempest.lib.common.api_version_request
   :members:

The api_version_utils module
""""""""""""""""""""""""""""

.. automodule:: tempest.lib.common.api_version_utils
   :members:
