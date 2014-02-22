# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.services.volume.json import backups_client


class BackupsClientXML(backups_client.BackupsClientJSON):
    """
    Client class to send CRUD Volume Backup API requests to a Cinder endpoint
    """
    TYPE = "xml"

    #TODO(gfidente): XML client isn't yet implemented because of bug 1270589
    pass
