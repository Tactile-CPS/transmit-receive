#!/home/joy/Documents/venv/bin/python3

# Date          : Oct-2022
# Author        : Deepak Choudhary and Joydeep Pal
# Description   : This script creates custom packets with VLAN tags.
# You can fill in VLAN IDs, PCP (Priority Code Point),
# and maybe add sequence numbers to a particular header field.
# Modified Date: Dec-2022, Feb,Apr,Sep-2023 - Joydeep Pal

import multiprocessing as mp

from scapy.all import get_if_list, get_if_hwaddr
from scapy.layers.l2 import Ether, Dot1Q
from scapy.layers.inet import IP, UDP, TCP
from scapy.packet import Raw
from scapy.utils import PcapWriter
import time
DEBUG = False


iface = 'enp2s0'  # 'lo', 'enp1s0np0', 'random', 'enp1s0f0'
srcmac = '90:e2:ba:0b:17:10'  # get_if_hwaddr(iface)
dstmac = '90:e2:ba:0b:17:11'  # '00:1b:21:c2:54:42'
srcip = '202.41.125.9'  # '100.1.10.10'  # '202.41.125,9'
dstip = '202.141.25.8'  # '100.1.10.11'  # '202.141.25.8'
srcportudp = 6000
# For test packets - 1 and 5, for production packets - 10 and 65536
# srcportudprange = srcportudp + 1
num_packets = 10

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
packetSizes = {100}  #, 500, 1000}

# To see fields,layers and fieldsizes, run scapy in terminal and
# call ls(IP()) for example
# 'ff:ff:ff:ff:ff:ff'


def generate_flow(packetLength, vlanid, dstportudp, priority, PcapSuffix):
    """ Create packet capture (.pcap) files"""
    PcapFileName = f'Traffic_Flow_vlan(' \
                   f'{vlanid})_packetsize({packetLength}B)_priority(' \
                   f'{priority}){PcapSuffix}_dev.pcap'

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
    customPayloadForExactPacketLength = packetLength - headerLength - extraCustomHeaderLength

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
            sport=srcportudp, dport=int(dstportudp))
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
