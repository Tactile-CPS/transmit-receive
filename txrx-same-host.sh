#!/bin/bash

# Description   : Broadly, it transmits and receives ST and BE flows using 2-port NIC on same end-host
# Author        : Joydeep Pal
# Date          : Nov-2022
# Date Modified : 10-Jan-2023, 18-May-2023, 06-Dec-2023 (Overhaul), 05-Jun-2024 (Overhaul)

# System Design:
#
# Port 1 --> || --> Port 2
#
# Each interface is given to its own network namespace. This is useful when iperf/ping commands
# are to be used on Tx and Rx ports in the same host. Otherwise these commands don't send packets
# out to the wire because kernel routes it internally. Run in root.
# Any Tx flow should go to another interface, same interface doesn't support both tx and rx.
set -e

# Define interface names
INTERFACE1="enp9s0f0"
INTERFACE2="enp9s0f1"

# Create network namespaces
ip netns add ns1
ip netns add ns2

# Assign interfaces to namespaces
ip link set $INTERFACE1 netns ns1
ip link set $INTERFACE2 netns ns2

# ---------------------------------
# Section 1: Configure IP addresses for the interfaces if no VLAN is needed
# ---------------------------------
ip netns exec ns1 ip addr add 192.168.1.1/24 dev $INTERFACE1
ip netns exec ns2 ip addr add 192.168.1.2/24 dev $INTERFACE2
ip netns exec ns1 ip link set $INTERFACE1 up
ip netns exec ns2 ip link set $INTERFACE2 up

COMMENT << HERE
# Optional : Capture packet for fine-grained analysis

# Start packet capture on individually for each flow at server (rx)
tshark -i $INTERFACE1 -a duration:7 -w /tmp/capture-experiment.pcap &
HERE

# Start iperf server for each flow
ip netns exec ns2 iperf -s -u -p 5001 > server1_stats.txt &
ip netns exec ns2 iperf -s -u -p 5002 > server2_stats.txt &
ip netns exec ns2 iperf -s -u -p 5001 -P 1 -i 1 -e --histogram > server1_stats.txt 2>&1 &
# ip netns exec ns2 iperf -s -u -B $INTERFACE2 -P 1 -e --histogram --jitter-histograms -i 1 > server1_stats.txt 2>&1 &

# Start iperf client for each flow
#ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5001 -t 10 -i 1 > client1_stats.txt &
#ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5001 -t 2 -i 1 -P 1 -b 10m -l 1000 -e --trip-times --tos 0
ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > client1_stats.txt &
#ip netns exec ns1 iperf -c $IP_TX -u -B $INTERFACE1 -p 5020 -t 2 -i 1 -P 1 -b 10m -l 1000 -e --trip-times --tos 0 > client1_stats.txt 2>&1 &
ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5002 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > client2_stats.txt &
#ip netns exec ns1 iperf -c $IP_TX -u -B $IFACE_TX -p 5021 -t 2 -i 1 -P 1 -b 10m -l 1000 -e --trip-times --tos 0 > client2_stats.txt 2>&1 &

# Wait for iperf to finish
wait

# ----------------------------------------
# Section 2: If VLAN interfaces are needed
# ----------------------------------------
ip netns exec ns1 ip link set $INTERFACE1 up
ip netns exec ns2 ip link set $INTERFACE2 up

ip netns exec ns1 ip link add link enp9s0f0 name enp9s0f0.11 type vlan id 11
ip netns exec ns1 ip link add link enp9s0f0 name enp9s0f0.12 type vlan id 12
ip netns exec ns1 ip addr add 192.168.1.11/24 dev enp9s0f0.11
ip netns exec ns1 ip addr add 192.168.2.12/24 dev enp9s0f0.12
ip netns exec ns1 ip link set enp9s0f0.11 up
ip netns exec ns1 ip link set enp9s0f0.12 up

ip netns exec ns2 ip link add link enp9s0f1 name enp9s0f1.11 type vlan id 11
ip netns exec ns2 ip link add link enp9s0f1 name enp9s0f1.12 type vlan id 12
ip netns exec ns2 ip addr add 192.168.1.21/24 dev enp9s0f1.11
ip netns exec ns2 ip addr add 192.168.2.22/24 dev enp9s0f1.12
ip netns exec ns2 ip link set enp9s0f1.11 up
ip netns exec ns2 ip link set enp9s0f1.12 up

## iperf server and client
ip netns exec ns2 iperf -s -B 192.168.1.21 -u -p 5001
ip netns exec ns2 iperf -s -B 192.168.2.22 -u -p 5002
ip netns exec ns1 iperf -c 192.168.1.21 -B 192.168.1.11 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0
ip netns exec ns1 iperf -c 192.168.2.22 -B 192.168.2.12 -u -p 5002 -t 10 -i 1 -b 10m -e --trip-times --tos 0

# ------------------------------------
# Section 2a: If capture is needed
# ------------------------------------
ip netns exec ns1 tshark -i enp9s0f0.11 -a duration:5 -s 118 -w /tmp/capture-experiment-tx1.pcap &
ip netns exec ns1 tshark -i enp9s0f0.12 -a duration:5 -s 118 -w /tmp/capture-experiment-tx2.pcap &
ip netns exec ns2 tshark -i enp9s0f1.11 -a duration:5 -s 118 -w /tmp/capture-experiment-rx1.pcap &
ip netns exec ns2 tshark -i enp9s0f1.12 -a duration:5 -s 118 -w /tmp/capture-experiment-rx2.pcap &
wait

# ------------------------------------
# Cleanup
# ------------------------------------

# Detach interfaces from namespaces
ip netns exec ns1 ip link set $INTERFACE1 down
ip netns exec ns2 ip link set $INTERFACE2 down
ip netns exec ns1 ip link set $INTERFACE1 netns 1
ip netns exec ns2 ip link set $INTERFACE2 netns 1

# Delete namespaces
ip netns delete ns1
ip netns delete ns2

COMMENT << HERE
# ------------------------------------
# Section 2a: If capture was needed for fine-grained analysis
# ------------------------------------
# Convert pcap to csv for analysis using python script

args="-T fields -E header=y -E separator=, \
-e udp.dstport -e frame.time_epoch -e frame.len \
-e iperf.tos -e iperf.id -e iperf.id2 -e iperf.sec -e iperf.usec"
# -e iperf.mport -e ip.src -e ip.dst -e ip.id -e udp.srcport -e udp.dstport  \

# Each flow's tx and rx should be put into {tx1,rx1,tx2,rx2,..}.csv
eval tshark -r /tmp/capture-experiment-tx1.pcap $args > /tmp/capture-experiment-tx1.csv &
eval tshark -r /tmp/capture-experiment-rx1.pcap $args > /tmp/capture-experiment-rx1.csv &
eval tshark -r /tmp/capture-experiment-tx2.pcap $args > /tmp/capture-experiment-tx2.csv &
eval tshark -r /tmp/capture-experiment-rx2.pcap $args > /tmp/capture-experiment-rx2.csv &
wait
./txrx-analysis.py
# or ./txrx-analysis-rxonly.py
HERE

echo '=================== Done !! ====================='
echo ' '

