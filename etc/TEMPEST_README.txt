To run:
-rename the /etc/tempest.conf.sample file to tempest.conf
-Set the fields in the file to values relevant to your system
-Set the "authentication" value (basic or keystone_v2 currently supported)
-from the root directory of the project, run "nosetests tempest/tests" to
 run all tests

TODO:
Use virtualenv to install all needed packages. Till then, the following
packages must be installed:
-httplib2
-testtools
-paramiko
-nose