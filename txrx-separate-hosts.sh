#!/bin/bash

# Description   : Generates, transmits and receives packet flows using 2-port NIC on separate end-hosts
# Author        : Joydeep Pal
# Date Created  : 06-Dec-2023
# Date Modified : 07-Jun-2024

# Define interface names
INTERFACE0="h1-eth0"
INTERFACE1="h2-eth0"

COMMENT << HERE
# ---------------------------------
# Section 1: Configure IP addresses for the interfaces if no VLAN is needed
# ---------------------------------
ip addr add 192.168.10.10/24 dev $INTERFACE0
ip addr add 192.168.10.20/24 dev $INTERFACE1
ip link set $INTERFACE0 up
ip link set $INTERFACE1 up

# If arp doesn't go through for some reason, fill arp cache
ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev enp4s0f0
ip neigh add 192.168.10.10 lladdr 90:e2:ba:f4:e0:e4 dev enp4s0f1
HERE

COMMENT << HERE
# ------------------------------------
# Section 1a: If capture is needed (optional)
# ------------------------------------
# Capture packets for fine-grained analysis
# Start packet capture individually for each flow at server (rx)
tshark -i $INTERFACE0 -a duration:15 -s 128 -w /tmp/expt-rx1.pcap &
tshark -i $INTERFACE1 -a duration:15 -s 128 -w /tmp/expt-rx2.pcap &
HERE

# Start iperf server for each flow
iperf -s -u -p 5010 > server1_stats.txt &
iperf -s -u -p 5011 > server2_stats.txt &
# iperf -s -u -B $INTERFACE1 -P 1 -e --histogram --jitter-histograms -i 1 > server1_stats.txt 2>&1 &

# Start iperf client for each flow
iperf -c '10.3.3.1' -u -p 5010 -B '10.6.6.2' -t 10 -P 1 -i 1 -b 1m -l 1000 --tos 0 -e --trip-times & # >> flow1-tx.csv & \
iperf -c '10.10.10.1' -u -p 5010 -B '10.10.10.2' -t 10 -P 1 -i 1 -b 1m -l 1000 --tos 0 -e --trip-times &

# Wait for iperf to finish
wait

COMMENT << HERE
# Optional : If capture enabled for fine-grained analysis,
# convert pcap to csv for analysis using python script'

tshark -r rx-exp1.pcapng -Y "udp.dstport==5010 && iperf.id2<=4000000000 && not icmp" -w /tmp/capture-experiment-rx.pcap
tshark -r tx-exp1.pcapng -Y "udp.dstport==5010 && iperf.id2<=4000000000 && not icmp" -w /tmp/capture-experiment-tx.pcap

args="-T fields -E header=y -E separator=, \
-e ip.src -e ip.dst -e ip.id -e udp.srcport -e udp.dstport \
-e frame.time_epoch -e frame.len \
-e iperf.id -e iperf.id2 -e iperf.sec -e iperf.usec -e iperf.bufferlen"  # -e data.len -e data.data

# Each flow's tx and rx should be put into {tx1,rx1,tx2,rx2,..}.csv
eval tshark -r /tmp/capture-experiment.pcap $args > tx1.csv &
eval tshark -r /tmp/capture-experiment.pcap $args > rx1.csv &
eval tshark -r /tmp/capture-experiment.pcap $args > tx2.csv &
wait

COMMANDS << HERE
echo 'Ping from h1 to h2'
ping -I 10.3.3.1 10.6.6.2 -c 5
echo 'Ping from h2 to h1'
ping -I 10.6.6.2 10.3.3.1 -c 5

echo 'iperf test from h2 (client) to h1 (server)'
iperf -s -B 10.3.3.1 -e -P 1
iperf -c 10.3.3.1 -B 10.6.6.2 -t 1 -P 1 -X -e --trip-times

echo 'iperf test from h1 (client) to h2 (server)'
iperf -s -B 10.6.6.2 -e -P 1
iperf -c 10.6.6.2 -B 10.3.3.1 -t 1 -P 1 -X -e --trip-times
HERE

echo '=================== Done !! ====================='
echo ' '

