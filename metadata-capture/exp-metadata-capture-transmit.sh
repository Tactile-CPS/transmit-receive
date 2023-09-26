#!/bin/bash

# Date		: 14-May-2023
# Author	: Joydeep Pal
# Description	: This script does the following tasks:
# 1. Starts packet capture at source 
# 2. Transmits and receives those custom packets (with space for metadata) on the same interface of the source PC
# 3. Then converts pcap to raw hexdump in the form of json using tshark, and then converts json to csv (one line for each packet)
# 4. Received packets have a different VLAN ID (identified by vlan.id=7, this modification is done by the switch's c_packetprocessing function), compared to transmitted packets and thus can be filtered out

source ~/Documents/tsn-project/configuration-variables.sh

# Script parameters:
PacketCount=30
pps=1
duration=$((PacketCount/pps))
LocalCaptureEthernetInterface=${TXPC_PORT}
TxRxfile=/tmp/txrx-metadata.pcap
pcap_file=${PROJECT_FOLDER_REMOTE}/data-pcap-csv/pcap/txrx-metadata-rtt-$Date.pcap

echo ''
echo User: $(whoami)
echo ''

tshark -i $LocalCaptureEthernetInterface -w $TxRxfile -a duration:$((duration+5)) &

echo '------------Transmitting packets----------------'
sleep 2
tcpreplay -i $LocalCaptureEthernetInterface -L $PacketCount --pps $pps \
~/Documents/vlan-pcap-files/NewFlows/Traffic_Flow_vlan\(2\)_packetsize\(1000B\)_Priority\(0\)_NoPrio_metadata_test11.pcap

ls -al /tmp/*.pcap

echo ' '
echo 'Analyzing packets ...'
sleep 1
Date=$(date "+%Y%m%d-%H")

mv $TxRxfile $pcap_file

echo 'Packet Count: Tx'
tshark -r $pcap_file -Y "frame.len == 1000 and vlan.id == 2" | wc -l
echo ' '
echo 'Packet Count: Rx'
tshark -r $pcap_file -Y "frame.len == 1000 and vlan.id == 7" | wc -l
echo ' '
tshark -r $pcap_file -Y "frame.len == 1000 and vlan.id == 7" \
-T jsonraw | jq -c '.[]._source.layers.frame_raw' \
> ${PROJECT_FOLDER_REMOTE}/data-pcap-csv/csv-temp/txrx-metadata-rtt.csv

exit

