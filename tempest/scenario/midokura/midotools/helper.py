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
__author__ = 'Albert'
__email__ = "albert.vico@midokura.com"


class Routetable:

    def __init__(self, *args):
        self.destination = None
        self.gateway = None
        self.genmask = None
        self.flags = None
        self.metric = None
        self.ref = None
        self.use = None
        self.iface = None
        if len(args) is 1:
            self.init_from_line(args[0])
            return

        (self.destination, self.gateway, self.iface) = args
        if len(args) > 3:
            self.genmask = args[3]

    def init_from_line(self, line):
        """
            default 10.10.1.1 0.0.0.0 U 0 0 0 eth0
        """
        cols = line.split(None)
        try:
            if len(cols) < 8 or not cols or cols[0] is "Destination":
                self.destination = None
                return
            self.destination = cols[0]
            self.gateway = cols[1]
            self.genmask = cols[2]
            self.flags = cols[3]
            self.metric = cols[4]
            self.ref = cols[5]
            self.use = cols[6]
            self.iface = cols[7]
        except Exception as error:
            raise error

    def __repr__(self):
        """Return a string representing the route"""
        return "dest=%-16s gw=%-16s mask=%-16s use=%s iface=%s" % \
               (self.destination,
                self.gateway,
                self.genmask,
                self.use,
                self.iface)

    def is_default_route(self):
        if self.destination is "default" \
                or "0.0.0.0" \
                and self.flags \
                is "UGS" \
                or "UC":
            return True
        else:
            return False

    def is_custom_route(self, destination, gateway):
        if self.destination == destination and self.gateway == gateway:
            return True
        else:
            return False

    @staticmethod
    def build_route_table(route_output):
        """
        ***Builds a route table from the route command output:***
        Kernel IP routing table
        Destination Gateway    Genmask        Flags Metric Ref Use Iface
        default     10.10.1.1  0.0.0.0        U     0      0   0   eth0
        10.10.1.0   *          255.255.255.0  U     0      0   0   eth0
        """
        rtable = []
        lines = route_output.split("\n")
        for line in lines[2:]:
            r = Routetable(line)
            if r.destination:
                rtable.append(r)

        return rtable