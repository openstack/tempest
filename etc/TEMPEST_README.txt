To run:
-rename the /etc/tempest.conf.sample file to tempest.conf
-Set the fields in the file to values relevant to your system
-Set the "authentication" value (basic or keystone_v2 currently supported)
-From the root directory of the project, run "./run_tests.sh" this will
create the venv to install the project dependencies and run nosetests tempest
to run all the tests
