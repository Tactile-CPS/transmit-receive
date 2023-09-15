#!/bin/bash

# Author: Joydeep Pal
# Date: 14 May 2023
# Description: This script does the following tasks:
# 1. Starts packet capture at source 
# 2. Transmits and receives those custom packets (with space for metadata) on the same interface of the source PC
# 3. Then converts pcap to raw hexdump in the form of json using tshark, and then converts json to csv (one line for each packet)
# 4. Received packets have a diferent VLAN ID (identified by vlan.id=7, this modification is done by the switch's c_packetprocessing function), compared to transmitted packets and thus can be filtered out

source ~/Documents/tsn-project/configuration-variables

# Script parameters:
PacketCount=30
pps=1
duration=$((PacketCount/pps))
LocalCaptureEthernetInterface=${TXPC_PORT}
TxRxfile=/tmp/metadata.pcap

echo ''
echo User: $(whoami)
echo ''

tshark -i $LocalCaptureEthernetInterface -w $TxRxfile -a duration:$((duration+5)) &

echo '------------Transmitting packets----------------'
sleep 2
tcpreplay -i $LocalCaptureEthernetInterface -L $PacketCount --pps $pps ${VLAN_PACKET_SOURCE_PATH}/NewFlows/Traffic_Flow_vlan\(2\)_packetsize\(1000B\)_Priority\(0\)_NoPrio_metadata_test11.pcap

ls -al /tmp/*.pcap

echo ' '
echo 'Analyzing packets ...'
sleep 1
Date=$(date "+%Y%m%d-%H")
pcap_file="${PROJECT_FOLDER}/data-pcap-csv/Test_2switch_MEts_sync_$Date.pcap"
mv $TxRxfile ${pcap_file}

echo 'Packet Count: Tx'
tshark -r ${pcap_file} -Y "frame.len == 1000 and vlan.id == 2" | wc -l
echo ' '
echo 'Packet Count: Rx'
tshark -r ${pcap_file} -Y "frame.len == 1000 and vlan.id == 7" | wc -l
echo ' '
tshark -r ${pcap_file} -Y "frame.len == 1000 and vlan.id == 7" \
-T jsonraw | jq -c '.[]._source.layers.frame_raw' > ${DATA_PCAP_CSV_PATH}/exp_rtt_packetdata_pcap_to_json.csv

exit

<< comment
# For executing above 2 commands on a specific file

echo 'Packet Count:'
tshark -r ../Networking_Experiments/Metadata_capture/pcap/Test_2switch_MEts_sync_20230514-14.pcap -Y "frame.len == 1000 and vlan.id == 5" | wc -l
echo ' '
tshark -r ../Networking_Experiments/Metadata_capture/pcap/Test_2switch_MEts_sync_20230514-14.pcap -Y "frame.len == 1000 and vlan.id == 5" \
-T jsonraw | jq -c '.[]._source.layers.frame_raw' > ../Networking_Experiments/Metadata_capture/pcap/sample_json_text_from_pcap_v2.csv
comment

