.. _clients:

Service Clients Usage
=====================

Tests make requests against APIs using service clients. Service clients are
specializations of the ``RestClient`` class. The service clients that cover the
APIs exposed by a service should be grouped in a service clients module.
A service clients module is python module where all service clients are
defined. If major API versions are available, submodules should be defined,
one for each version.

The ``ClientsFactory`` class helps initializing all clients of a specific
service client module from a set of shared parameters.

The ``ServiceClients`` class provides a convenient way to get access to all
available service clients initialized with a provided set of credentials.

-----------------------------
The clients management module
-----------------------------

.. automodule:: tempest.lib.services.clients
   :members:

------------------------------
Compute service client modules
------------------------------

.. toctree::
   :maxdepth: 2

   service_clients/compute_clients
