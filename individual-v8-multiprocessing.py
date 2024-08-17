#!/usr/bin/env python

# Date          : Oct-2022
# Author        : Joydeep Pal
# Description   : This script creates custom packets with VLAN tags.
# You can fill in VLAN IDs, PCP (Priority Code Point),
# and add sequence numbers to a iperf header field.
# Modified Date: Dec-2022, Feb,Apr,Sep-2023, Aug-2024 - Joydeep Pal

import multiprocessing as mp

from scapy.all import get_if_list, get_if_hwaddr
from scapy.layers.l2 import Ether, Dot1Q
from scapy.layers.inet import IP, UDP, TCP
from scapy.packet import Raw, Packet
from scapy.utils import PcapWriter
from scapy.fields import ShortField, IntField
import time
DEBUG = True

iface  = 'enp2s0'  # 'lo', 'enp1s0np0', 'random', 'enp1s0f0'
srcmac = '90:e2:ba:0b:17:10'  # get_if_hwaddr(iface)
dstmac = '90:e2:ba:0b:17:11'  # '00:1b:21:c2:54:42'
srcip  = '100.1.10.10'  # '202.41.125,9'
dstip  = '100.1.10.11'  # '202.141.25.8'
srcportudp = 6000
# For test packets - 1 and 5, for production packets - 10 and 65536
num_packets = 655360

# Change the vlan tag to generate desired vlan tagged packet
# Change the udp destination port to generate desired udp packet
vlanid_to_dstportudp = {
    '10': '5010',
    '11': '5011'
}
vlanid_to_priority = {
    '10': '0',
    '11': '1'
}
packetSizes = {128}  #, 512, 1024}


class IPERF(Packet):
    fields_desc = [
        IntField("iperf_seq", 0),
        IntField("iperf_sec", 0),
        IntField("iperf_usec", 0),
        IntField("iperf_seq2", 0),
        IntField("iperf_flags", 0),
        IntField("iperf_numthreads", 0),
        IntField("iperf_mport", 0),
        IntField("iperf_bufferlen", 0),
        IntField("iperf_mwinband", 0),
        IntField("iperf_mamount", 0),
        IntField("iperf_type", 0),
        IntField("iperf_length", 0),
        ShortField("iperf_upperflags", 0),
        ShortField("iperf_lowerflags", 0),
        IntField("iperf_version_u", 0),
        IntField("iperf_version_l", 0),
        ShortField("iperf_reserved", 0),
        ShortField("iperf_tos", 0),
        IntField("iperf_irate", 0),
        IntField("iperf_urate", 0),
        IntField("iperf_tcpwriteprefetch", 0)
    ]

# To see fields,layers and fieldsizes, run scapy in terminal and
# call ls(IP()) for example
# 'ff:ff:ff:ff:ff:ff'


def generate_flow(packetLength, vlanid, dstportudp, priority, PcapSuffix):
    """ Create packet capture (.pcap) files"""
    PcapFileName = f'Traffic_Flow_vlan_' \
                   f'{vlanid}_packetsize_{packetLength}B_priority_' \
                   f'{priority}_{PcapSuffix}_dev.pcap'

    # Packet Length:
    # len(Ether()) = 14
    # len(DOt1Q()) = 4
    # len(IP()) = 20
    # len(UDP()) = 8
    # HeaderLength = 14 + 4 + 20 + 8 = 46 bytes
    # iperf length = 76
    # For example - for PacketLength = 1000:
    # PacketLength = 930 + 46 headers + 24 data = 1000 bytes
    headerLength = 46
    extraCustomHeaderLength = 82
    customPayloadForExactPacketLength = packetLength - headerLength - extraCustomHeaderLength

    CustomPayload = ""
    while len(CustomPayload) < customPayloadForExactPacketLength:
        CustomPayload += "packetgeneration"

    writetoPcap = PcapWriter(PcapFileName)  # opened file to write

    for packetSeqNo in range(num_packets):
        packetPayload = f"tstpkt{CustomPayload}"
        packet = Ether(
            src=srcmac, dst=dstmac) / Dot1Q(
            prio=int(priority), vlan=int(vlanid)) / IP(
            src=srcip, dst=dstip, proto=17) / UDP(  # id=packetSeqNo, proto=17
            sport=srcportudp, dport=int(dstportudp)) / IPERF(iperf_seq=packetSeqNo)
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
            # generate_flow(packetLength, vlanid, dstportudp, priority, '_NoPrio')

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
