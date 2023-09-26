#!/home/joy/Documents/venv/bin/python3

# Date          : 03-May-2023
# Author        : Joydeep Pal
# Modified Date : 26-Sep-2023
# Description   : This script creates custom packets with VLAn tags and space for metadata.
# Each packet can be identified using packet number in payload.
# You can fill in VLAN IDs, PCP (Priority Code Point),
# udp.dstport, vlan.id, priority are mapped.

import multiprocessing as mp

from scapy.all import BitField, Packet
from scapy.all import get_if_list, get_if_hwaddr
from scapy.layers.l2 import Ether, Dot1Q
from scapy.layers.inet import IP, UDP, TCP
from scapy.packet import Raw
from scapy.utils import PcapWriter
import time
DEBUG = False


class MetadataHeader(Packet):
    name = "MetadataHeader"
    fields_desc = [
        BitField("timestamp1", 0, 64),
        BitField("timestamp2", 0, 64),
        BitField("timestamp3", 0, 64),
        BitField("timestamp4", 0, 64),
        BitField("timestamp5", 0, 64),
        BitField("timestamp6", 0, 64),
        BitField("timestamp7", 0, 64),
        BitField("timestamp8", 0, 64),
        BitField("timestamp9", 0, 64),
        BitField("timestamp10", 0, 64)
    ]
    def mysummary(self):
        return self.sprintf("metadata")


iface = 'enp1s0f0'  # 'lo', 'enp1s0np0', 'random'
srcmac = '90:e2:ba:0b:17:10'  # get_if_hwaddr(iface)
dstmac = '90:e2:ba:0b:17:11'  # '00:1b:21:c2:54:42'
srcip = '100.1.10.10'
dstip = '100.1.10.11'
srcportudp = 6000
# For test packets - 1 and 5, for production packets - 10 and 65536
# srcportudprange = srcportudp + 1
num_packets = 2

# Change the vlan tag to generate desired vlan tagged packet
# Change the udp destination port to generate desired udp packet
vlanid_to_dstportudp = {
    '2': '3002',
    '3': '3003',
    '4': '3004'
}
vlanid_to_priority = {
    '2': '0',
    '3': '1',
    '4': '2'
}
packetSizes = {200, 500, 1000}

# To see fields,layers and fieldsizes, run scapy in terminal and
# call ls(IP()) for example
# 'ff:ff:ff:ff:ff:ff'


def generate_flow(packetLength, vlanid, dstportudp, priority, PcapSuffix):
    """ Create packet capture (.pcap) files"""
    PcapFileName = f'Traffic_Flow_vlan(' \
                   f'{vlanid})_packetsize({packetLength}B)_priority(' \
                   f'{priority}){PcapSuffix}_with_metadata_header.pcap'

    # Packet Length:
    # len(Ether()) = 14
    # len(DOt1Q()) = 4
    # len(IP()) = 20
    # len(UDP()) = 8
    # HeaderLength = 14 + 4 + 20 + 8 = 46 bytes
    # For example - for PacketLength = 1000:
    # PacketLength = 930 + 46 headers + 24 data = 1000 bytes
    headerLength = 46
    extraCustomHeaderLength = 24
    MetadataHeaderLength = 80  # 10 * 8 bytes
    customPayloadForExactPacketLength = packetLength - headerLength - extraCustomHeaderLength - MetadataHeaderLength

    CustomPayload = ""
    while len(CustomPayload) < customPayloadForExactPacketLength:
        CustomPayload += "test0"

    writetoPcap = PcapWriter(PcapFileName)  # opened file to write

    for packetSeqNo in range(num_packets):
        packetPayload = f"Packet_Num_{packetSeqNo:012d}_{CustomPayload}"
        packet = Ether(
            src=srcmac, dst=dstmac) / Dot1Q(
            prio=int(priority), vlan=int(vlanid)) / IP(
            src=srcip, dst=dstip, proto=17) / UDP(  # id=packetSeqNo, proto=17
            sport=srcportudp, dport=int(dstportudp)) / MetadataHeader(
            timestamp1=797651088306, timestamp2=797651088308,
            timestamp3=797651088310, timestamp4=797651088311,
            timestamp5=797651088312)
        # IP proto=253 (used for testing and experimentation, used in this code if UDP header is not used above)

        packet = packet / Raw(load=packetPayload)

        if DEBUG:
            if packetSeqNo in {1}:
                packet.show2()

        # Write the packets to a pcap file, can be used with tcpreplay later
        writetoPcap.write(packet)


def main():
    # Create parallel tasks = No. of cpu cores - 2
    # (for doing other work, otherwise it will hang)
    pool = mp.Pool(processes=mp.cpu_count() - 2)

    items = []
    ''' Define packets with no priority assigned '''
    for vlanid, dstportudp in vlanid_to_dstportudp.items():
        for packetLength in packetSizes:
            priority = 0
            print(vlanid, dstportudp, packetLength, priority, '_NoPrio')
            items.append((packetLength, vlanid, dstportudp, priority, '_NoPrio'))
            # generate_flow(PacketLength, vlanID, UDPdstport, priority, '_NoPrio')

    ''' Define packets with priority assigned '''
    for vlanid, dstportudp in vlanid_to_dstportudp.items():
        for packetLength in packetSizes:
            priority = vlanid_to_priority.get(vlanid)
            print(vlanid, dstportudp, packetLength, priority)
            items.append((packetLength, vlanid, dstportudp, priority, ''))

    for result in pool.starmap(generate_flow, items):
        print(result)


if __name__ == '__main__':
    main()
