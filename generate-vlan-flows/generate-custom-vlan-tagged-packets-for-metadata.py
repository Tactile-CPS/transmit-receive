#!/home/zenlab/venv/bin/python3

# Date		: 03-May-2023
# Author	: Joydeep Pal
# Description	: This script creates custom packets with space for metadata.
# Creates 65536 packets of UDPsrcport of 6000, 6001 etc. Thus, each packet can be identified using ip.id, udp.srcport. 
# udp.dstport, vlan.id, priority are mapped.

from scapy.all import *
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
        BitField("timestamp9", 0, 64)
    ]
    def mysummary(self):
        return self.sprintf("metadata")

iface = 'random'  # 'lo', 'enp1s0np0', 'enp1s0f0'
srcmac = '00:1b:21:c2:54:11'  # get_if_hwaddr(iface)
dstmac = '00:1b:21:c2:54:12'  # '00:1b:21:c2:54:42'
UDPsrcport = 6000
UDPsrcportrange = UDPsrcport + 1
IPsrc = '100.1.10.10'
IPdst = '100.1.10.11'

# Change the vlan tag to generate desired vlan tagged packet
# Change the udp destination port to generate desired udp packet
vlanID_to_UDPdstport = {
    '2': '3002',
    '3': '3003'
}
vlanID_to_Priority = {
    '2': '0',
    '3': '1'
}
WhichPacketSizes = {500, 1000}

# Current Command to run: "./filename.py"

# To see fields,layers and fieldsizes, run scapy in terminal and
# call ls(IP()) for example
# 'ff:ff:ff:ff:ff:ff'


def generate_flow(PacketLength, vlanID, UDPdstport, Priority, PcapSuffix):
    """ Create packet capture (.pcap) files"""
    PcapFileName = f'Traffic_Flow_vlan(' \
                   f'{vlanID})_packetsize({PacketLength}B)_Priority(' \
                   f'{Priority}){PcapSuffix}_metadata_test11.pcap'

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
	MetadataHeaderLength = 40 # 5 * 8 bytes
    CustomPayloadForExactPacketLength = PacketLength - HeaderLength - ExtraCustomHeaderLength - MetadataHeaderLength

    CustomPayload = ""
    while len(CustomPayload) < CustomPayloadForExactPacketLength:
        CustomPayload += "test "

    writetoPcap = PcapWriter(PcapFileName)  # opened file to write

    for UDPsrcport_ in range(UDPsrcport, UDPsrcportrange):
        for PacketSequenceNo in range(65536):
            # Packet_Content = 'Packet_Num_' + f'{PacketSequenceNo:012d}' + '_' + CustomPayload
            Packet_Content = f"Packet_Num_{PacketSequenceNo:012d}_{CustomPayload}"
            packet = Ether(
                src=srcmac, dst=dstmac) / Dot1Q(
                prio=int(Priority), vlan=int(vlanID)) / IP(
                src=IPsrc, dst=IPdst, id=PacketSequenceNo, proto=17) / UDP(
                sport=UDPsrcport_, dport=int(UDPdstport)) / MetadataHeader(
                timestamp1=797651088306, timestamp2=797651088308, timestamp3=797651088310, timestamp4=797651088311, timestamp5=797651088312)
            # IP proto=253 (used for testing and experimentation, used in this code if UDP header is not used above)

            packet = packet / Raw(load=Packet_Content)

            if DEBUG:
                if (PacketSequenceNo in {1}) and (UDPsrcport in {6000}):
                    packet.show2()

            # Write the packets to a pcap file, can be used with tcpreplay later
            writetoPcap.write(packet)


def main():


    ''' Define packets with no priority assigned '''
    for vlanID, UDPdstport in vlanID_to_UDPdstport.items():
        for PacketLength in WhichPacketSizes:
            Priority = 0
            print(vlanID, UDPdstport, PacketLength, Priority, '_NoPrio')
            # items.append((PacketLength, vlanID, UDPdstport, Priority, '_NoPrio'))
            generate_flow(PacketLength, vlanID, UDPdstport, Priority, '_NoPrio')

    ''' Define packets with priority assigned '''
    # for vlanID, UDPdstport in vlanID_to_UDPdstport.items():
    #     for PacketLength in WhichPacketSizes:
    #         Priority = vlanID_to_Priority.get(vlanID)
    #         print(vlanID, UDPdstport, PacketLength, Priority)
    #         items.append((PacketLength, vlanID, UDPdstport, Priority, ''))


if __name__ == '__main__':
    main()
