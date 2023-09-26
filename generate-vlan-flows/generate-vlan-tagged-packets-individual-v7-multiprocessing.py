#!/home/joy/Documents/venv/bin/python3

# Date		: Oct-2022
# Author	: Deepak Choudhary and Joydeep Pal
# Description	: This script creates custom packets with VLAN tags.
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


iface = 'random'  # 'lo', 'enp1s0np0', 'enp1s0f0'
srcmac = '11:11:11:11:11:11'  # get_if_hwaddr(iface)
dstmac = '11:11:11:11:11:12'  # '00:1b:21:c2:54:42'
IPsrc = '100.1.10.10'
IPdst = '100.1.10.11'
UDPsrcport = 6000
# For test packets - 1 and 5, for production packets - 10 and 65536
UDPsrcportrange = UDPsrcport + 10
NumPackets = 65536

# Change the vlan tag to generate desired vlan tagged packet
# Change the udp destination port to generate desired udp packet
vlanID_to_UDPdstport = {
    '2': '3002',
    '3': '3003',
    '4': '3004'
}
vlanID_to_Priority = {
    '2': '0',
    '3': '1',
    '4': '2'
}
WhichPacketSizes = {100, 500, 1000}

# Current Command to run: "./generate_vlan_tagged_packets_individual_v7_multiprocessing.py"

# To see fields,layers and fieldsizes, run scapy in terminal and
# call ls(IP()) for example
# 'ff:ff:ff:ff:ff:ff'


def generate_flow(PacketLength, vlanID, UDPdstport, Priority, PcapSuffix):
    """ Create packet capture (.pcap) files"""
    PcapFileName = f'Traffic_Flow_vlan(' \
                   f'{vlanID})_packetsize({PacketLength}B)_Priority(' \
                   f'{Priority}){PcapSuffix}_dev.pcap'

    # Packet Length:
    # len(Ether()) = 14
    # len(DOt1Q()) = 4
    # len(IP()) = 20
    # len(UDP()) = 8
    # HeaderLength = 14 + 4 + 20 + 8 = 46 bytes
    # For example - for PacketLength = 1000:
    # PacketLength = 930 + 46 headers + 24 data = 1000 bytes
    HeaderLength = 46
    ExtraCustomHeaderLength = 24
    CustomPayloadForExactPacketLength = PacketLength - HeaderLength - ExtraCustomHeaderLength

    CustomPayload = ""
    while len(CustomPayload) < CustomPayloadForExactPacketLength:
        CustomPayload += "test "

    writetoPcap = PcapWriter(PcapFileName)  # opened file to write

    for UDPsrcport_ in range(UDPsrcport, UDPsrcportrange):
        for PacketSequenceNo in range(NumPackets): 
            Packet_Content = f"Packet_Num_{PacketSequenceNo:012d}_{CustomPayload}"
            packet = Ether(
                src=srcmac, dst=dstmac) / Dot1Q(
                prio=int(Priority), vlan=int(vlanID)) / IP(
                src=IPsrc, dst=IPdst, id=PacketSequenceNo, proto=17) / UDP(
                sport=UDPsrcport_, dport=int(UDPdstport))
            # IP proto=253 (used for testing and experimentation, used in this code if UDP header is not used above)

            packet = packet / Raw(load=Packet_Content)

            if DEBUG:
                if (PacketSequenceNo in {1}) and (UDPsrcport in {6000}):
                    packet.show2()

            # Write the packets to a pcap file, can be used with tcpreplay later
            writetoPcap.write(packet)


def main():
    # Create parallel tasks = No. of cpu cores - 2
    # (for doing other work, otherwise it will hang)
    pool = mp.Pool(processes=mp.cpu_count() - 2)

    items = []
    ''' Define packets with no priority assigned '''
    for vlanID, UDPdstport in vlanID_to_UDPdstport.items():
        for PacketLength in WhichPacketSizes:
            Priority = 0
            print(vlanID, UDPdstport, PacketLength, Priority, '_NoPrio')
            items.append((PacketLength, vlanID, UDPdstport, Priority, '_NoPrio'))
            # generate_flow(PacketLength, vlanID, UDPdstport, Priority, '_NoPrio')

    ''' Define packets with priority assigned '''
    for vlanID, UDPdstport in vlanID_to_UDPdstport.items():
        for PacketLength in WhichPacketSizes:
            Priority = vlanID_to_Priority.get(vlanID)
            print(vlanID, UDPdstport, PacketLength, Priority)
            items.append((PacketLength, vlanID, UDPdstport, Priority, ''))

    for result in pool.starmap(generate_flow, items):
        print(result)


if __name__ == '__main__':
    main()
