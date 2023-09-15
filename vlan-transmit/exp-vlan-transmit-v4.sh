#!/bin/bash

# Author: Joydeep Pal
# Date: Nov 2022
# Date Modified: 10 Jan, 18 May 2023
# Description: Broadly, it transmits ST and BE flows to the destination end-host.
# Flows are defined using VLAN IDs.
# Flows travel via one or multiple NFP's running a firmware
# either NIC firmware (nic_firmware) or our custom Micro-C program firmware.
# Use relevant python script to analyze the performance.

# It uses ssh to run remote commands and
# you should have set up ssh and configured passwordless ssh.

# System Design:
#                                              ____________________
# (PC#1) MultiNIC_TX_port --> one or multiple | NFP_P1 --> NFP_P0 | --> (PC #2) MultiNIC_RX_port
#                                             ---------------------

source ~/Documents/tsn-project/configuration-variables.sh

# Script parameters:

BandwidthSTFlow=10M # 10M # 6.6M # 3.3M
BandwidthBEFlow=10M
Duration=5
DurationCapture=$(($Duration+5))

#LocalCaptureInterfaceIP=20.20.20.20
#RemoteCaptureInterfaceIP=20.20.20.21

TXfile=/tmp/tx-exp.pcap
RXfile=/tmp/rx-exp.pcap

echo ''
echo User: $(whoami)
echo ''

echo 'Step 1: Start packet capture on tx and rx'
ssh $RXPC_IP "tshark -i $RXPC_PORT -a duration:$DurationCapture -w $RXfile" &
tshark -i $TXPC_PORT -a duration:$DurationCapture -w $TXfile &

sleep 1

echo ' '
echo 'Step 2: Start packet tx (Mixed VLAN Traffic)'
echo 'Next two are for custom MicroC programs'
tcpreplay -i $TXPC_PORT -M $BandwidthSTFlow --duration=$Duration '~/Documents/vlan-pcap-files/NewFlows/Traffic_Flow_vlan(2)_packetsize(100B)_Priority(0)_NoPrio_test8.pcap' &
tcpreplay -i $TXPC_PORT -M $BandwidthBEFlow --duration=$Duration '~/Documents/vlan-pcap-files/NewFlows/Traffic_Flow_vlan(3)_packetsize(100B)_Priority(0)_NoPrio_test8.pcap'
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthBEFlow --duration=$Duration '../VLAN_PCAP_Files/NewFlows/Traffic_Flow_vlan(4)_packetsize(1000B)_Priority(0)_NoPrio_test8.pcap' &
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthSTFlow --duration=$Duration '../VLAN_PCAP_Files/NewFlows/VLAN_2_packets_Size_1000B_NoPrio_test4.pcap' &
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthBEFlow --duration=$Duration '../Networking_Experiments/VLAN_PCAP_Files/ArchiveFlows/VLAN_3_packets_Size_1000B_NoPrio_test4.pcap' &
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthTest --duration=$Duration ../Networking_Experiments/VLAN_PCAP_Files/Equally_Mixed_VLAN_packets_fixed_data_length.pcap
echo 'Next two are for running on nic_firmware'
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthSTFlow --duration=$Duration '../Networking_Experiments/VLAN_PCAP_Files/ArchiveFlows/iperf_3002_VLAN_2_packets_Size_1000B_test6.pcap' &
#tcpreplay -i $LocalCaptureEthernetInterface -M $BandwidthBEFlow --duration=$Duration '../Networking_Experiments/VLAN_PCAP_Files/ArchiveFlows/iperf_3003_VLAN_3_packets_Size_1000B_test6.pcap'

echo ' '
echo 'Step 3: Check if packet capture successful by checking if file exists in remote node'
sleep 3
ssh $RXPC_IP "ls -al /tmp/ | grep rx" # or "ls -al $RXfile"

echo 'Step 4: Transfer Tx capture from remote to local system for analysis'
scp -C $RXPC_IP:$RXfile $RXfile

echo 'Step 5: Convert pcap to csv for automated analysis with python'
args="-T fields -E header=y -E separator=, -e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority \
-e udp.srcport -e udp.dstport -e frame.time_epoch -e frame.len"
eval tshark -r $RXfile $args > /tmp/RXv1.csv &
eval tshark -r $TXfile $args > /tmp/TXv1.csv

echo 'Step 6: Process using python script'
./latency-v6.py $BandwidthSTFlow $BandwidthBEFlow $Duration

echo 'Done !!'
echo ' '
