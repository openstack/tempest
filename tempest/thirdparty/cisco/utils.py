# Copyright 2015 OpenStack Foundation
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

import UcsSdk as ucssdk


class UCSMClient(object):
    """
    UCSM Facade class. Interacts with UCS Manager.
    """

    lan_path = "fabric/lan"
    vlan_path = lan_path + "/net-OS-{id}"
    eth_path = "{service_profile_dn}/ether-{eth_name}"
    eth_vlan_path = eth_path + "/if-OS-{vlan_id}"

    def __init__(self, ip, username, password):
        self._handle = None
        self._ip = ip
        self._username = username
        self._password = password

    @property
    def handle(self):
        if self._handle is None:
            self._handle = ucssdk.UcsHandle()
        return self._handle

    def login(self):
        self.handle.Login(self._ip, self._username, self._password)

    def logout(self):
        if self._handle:
            self._handle.Logout()

    def _get_service_profile(self, dn):
        return self.handle.GetManagedObject(
            None,
            ucssdk.LsServer.ClassId(),
            {ucssdk.LsServer.DN: dn})

    def get_vnic_ether(self, service_profile, dn):
        return self.handle.GetManagedObject(
            service_profile, ucssdk.VnicEther.ClassId(),
            {ucssdk.VnicEther.DN: dn}, True)

    def get_vnic_ether_if(self, parent):
        return self.handle.GetManagedObject(
            parent, ucssdk.VnicEtherIf.ClassId())

    def _get_lan_cloud(self):
        return self.handle.GetManagedObject(
            None, ucssdk.FabricLanCloud.ClassId(),
            {ucssdk.FabricLanCloud.DN: self.lan_path})

    def get_vlan_profile(self, vlan_id):
        lan_cloud = self._get_lan_cloud()
        return self.handle.GetManagedObject(
            lan_cloud, ucssdk.FabricVlan.ClassId(),
            {ucssdk.FabricVlan.DN: self.vlan_path.format(id=vlan_id)})

    def get_ether_vlan(self, service_profile_dn, eth_name, vlan_id):
        sp = self._get_service_profile(service_profile_dn)
        eth = self.get_vnic_ether(sp, self.eth_path.format(
            service_profile_dn=service_profile_dn, eth_name=eth_name))
        return self.handle.GetManagedObject(
            eth, ucssdk.VnicEtherIf.ClassId(),
            {ucssdk.VnicEtherIf.DN: self.eth_vlan_path.format(
                service_profile_dn=service_profile_dn,
                eth_name=eth_name,
                vlan_id=vlan_id)})

    def get_port_profile(self, dn):
        return self.handle.GetManagedObject(
            None, ucssdk.VnicProfile.ClassId(),
            {ucssdk.VnicProfile.DN: dn})
