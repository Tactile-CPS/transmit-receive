#!/bin/bash

# -------------------------------------------------------
# Description   : Generates, transmits and receives packet flows using 2-port NIC on same end-host
# Author        : Joydeep Pal
# Date          : Nov-2022
# Date Modified : 10-Jan-2023, 18-May-2023, 06-Dec-2023 (Overhaul), 05-Jun-2024 (Overhaul)
# -------------------------------------------------------

# -------------------------------------------------------
# Details:
# System Design:
#
# Port 1 --> || --> Port 2
#
# Each interface is assigned to a network namespace. This is useful when iperf/ping commands
# are to be used on Tx and Rx ports in the same host. Otherwise these commands don't send packets
# out to the wire because kernel routes it internally. Run in root.
# Any Tx flow should go to another interface, same interface doesn't support both tx and rx.
# -------------------------------------------------------


# Define interface names
INTERFACE0="enp4s0f0"
INTERFACE1="enp4s0f1"
: '
# Create network namespaces
ip netns add ns0
ip netns add ns1

# Assign interfaces to namespaces
ip link set $INTERFACE0 netns ns0
ip link set $INTERFACE1 netns ns1
'

COMMENT << HERE
# ---------------------------------
# Section 1: Configure IP addresses for the interfaces if no VLAN is needed
# ---------------------------------
ip netns exec ns0 ip addr add 192.168.10.10/24 dev $INTERFACE0
ip netns exec ns1 ip addr add 192.168.10.20/24 dev $INTERFACE1
ip netns exec ns0 ip link set $INTERFACE0 up
ip netns exec ns1 ip link set $INTERFACE1 up

# If arp doesn't go through for some reason, fill arp cache
ip netns exec ns0 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev enp4s0f0
ip netns exec ns1 ip neigh add 192.168.10.10 lladdr 90:e2:ba:f4:e0:e4 dev enp4s0f1
HERE

COMMENT << HERE
# ------------------------------------
# Section 1a: If capture is needed (optional)
# ------------------------------------
# Capture packets for fine-grained analysis
# Start packet capture individually for each flow at server (rx)
tshark -i $INTERFACE0 -a duration:7 -s 128 -w /tmp/tmpexp/expt-rx1.pcap &
tshark -i $INTERFACE1 -a duration:7 -s 128 -w /tmp/tmpexp/expt-tx1.pcap &
HERE

: '
# Start iperf server & iperf client for each flow
ip netns exec ns1 iperf -s -u -p 5010 -i 1 > server1_stats.txt &
ip netns exec ns1 iperf -s -u -p 5011 -i 1 > server2_stats.txt &
# ip netns exec ns1 iperf -s -u -B $INTERFACE0 -P 1 -e --histogram --jitter-histograms -i 1 > /tmp/tmpexp/erver1_stats.txt 2>&1 &

ip netns exec ns0 iperf -c 192.168.10.20 -u -p 5010 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > /tmp/tmpexp/client1_stats.txt &
ip netns exec ns0 iperf -c 192.168.10.20 -u -p 5011 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > /tmp/tmpexp/client2_stats.txt &
#ip netns exec ns0 iperf -c 192.168.10.20 -u -B $INTERFACE1 -p 5010 -t 10 -i 1 -b 10m -P 1 -l 1000 -e --trip-times --tos 0 > /tmp/tmpexp/client1_stats.txt 2>&1 &
# Wait for iperf to finish
wait
'

: '
# ----------------------------------------
# Section 2: If VLAN interfaces are needed
# ----------------------------------------
ip netns exec ns0 ip link set $INTERFACE0 up
ip netns exec ns1 ip link set $INTERFACE1 up

ip netns exec ns0 ip link add link $INTERFACE0 name $INTERFACE0.10 type vlan id 10
ip netns exec ns0 ip link add link $INTERFACE0 name $INTERFACE0.11 type vlan id 11
ip netns exec ns0 ip addr add 192.168.10.10/24 dev $INTERFACE0.10
ip netns exec ns0 ip addr add 192.168.11.10/24 dev $INTERFACE0.11
ip netns exec ns0 ip link set $INTERFACE0.10 up
ip netns exec ns0 ip link set $INTERFACE0.11 up

ip netns exec ns1 ip link add link $INTERFACE1 name $INTERFACE1.10 type vlan id 10
ip netns exec ns1 ip link add link $INTERFACE1 name $INTERFACE1.11 type vlan id 11
ip netns exec ns1 ip addr add 192.168.10.20/24 dev $INTERFACE1.10
ip netns exec ns1 ip addr add 192.168.11.20/24 dev $INTERFACE1.11
ip netns exec ns1 ip link set $INTERFACE1.10 up
ip netns exec ns1 ip link set $INTERFACE1.11 up

## Configure arp
ip netns exec ns0 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev $INTERFACE0.10
ip netns exec ns0 ip neigh add 192.168.11.20 lladdr 90:e2:ba:f4:e0:e5 dev $INTERFACE0.11
ip netns exec ns1 ip neigh add 192.168.10.10 lladdr 90:e2:ba:f4:e0:e4 dev $INTERFACE1.10
ip netns exec ns1 ip neigh add 192.168.11.10 lladdr 90:e2:ba:f4:e0:e4 dev $INTERFACE1.11
'

# ------------------------------------
# Section 3 : Run - both tx from same port
# ------------------------------------
# ------------------------------------
# Section 3a: If capture is needed
# ------------------------------------
#ip netns exec ns0 tshark -i enp4s0f0.5 -f "vlan and udp dst port 5000" -a duration:12 -s 128 -w /tmp/expt-tx1.pcap &
ip netns exec ns0 tshark -i $INTERFACE0.10 -f "udp dst port 5010" -a duration:15 -s 128 -w /tmp/tmpexp/expt-rx1.pcap &
ip netns exec ns0 tshark -i $INTERFACE0.11 -f "udp dst port 5011" -a duration:15 -s 128 -w /tmp/tmpexp/expt-rx2.pcap &
ip netns exec ns1 tshark -i $INTERFACE1.10 -f "udp dst port 5010" -a duration:15 -s 128 -w /tmp/tmpexp/expt-tx1.pcap &
ip netns exec ns1 tshark -i $INTERFACE1.11 -f "udp dst port 5011" -a duration:15 -s 128 -w /tmp/tmpexp/expt-tx2.pcap &
# iperf server and client - both tx from same port ns1
ip netns exec ns0 iperf -s -B 192.168.10.10 -u -p 5010 -i 1 -t 12 -z > /tmp/tmpexp/server1_stats.txt &
ip netns exec ns0 iperf -s -B 192.168.11.10 -u -p 5011 -i 1 -t 12 -z > /tmp/tmpexp/server2_stats.txt &
sleep 2
ip netns exec ns1 iperf -c 192.168.10.10 -B 192.168.10.20 -u -p 5010 -t 5 -l 125 -z -i 1 -b 100m -e --trip-times --tos 0 --no-udp-fin > /tmp/tmpexp/client1_stats.txt &
ip netns exec ns1 iperf -c 192.168.11.10 -B 192.168.11.20 -u -p 5011 -t 5 -l 125 -z -i 1 -b 100m -e --trip-times --tos 0 --no-udp-fin > /tmp/tmpexp/client2_stats.txt &
wait

: '
# ------------------------------------
# Section 3b : Run - cross-connection
# ------------------------------------
# ------------------------------------
# Section 3ba: If capture is needed
# ------------------------------------
#ip netns exec ns0 tshark -i enp4s0f0.5 -f "vlan and udp dst port 5000" -a duration:12 -s 128 -w /tmp/expt-tx1.pcap &
ip netns exec ns0 tshark -i $INTERFACE0.10 -f "udp dst port 5010" -a duration:15 -s 128 -w /tmp/tmpexp/expt-rx1.pcap &
ip netns exec ns1 tshark -i $INTERFACE1.10 -f "udp dst port 5010" -a duration:15 -s 128 -w /tmp/tmpexp/expt-tx1.pcap &
sleep 2

## iperf server and client - each tx on each port
ip netns exec ns0 iperf -s -B 192.168.10.10 -u -p 5010 -i 1 -t 12 -z > /tmp/tmpexp/server1_stats.txt &
ip netns exec ns1 iperf -s -B 192.168.11.20 -u -p 5011 -i 1 -t 12 -z > /tmp/tmpexp/server2_stats.txt &
sleep 1
ip netns exec ns1 iperf -c 192.168.10.10 -B 192.168.10.20 -u -p 5010 -t 10 -P 1 -l 1000 -z -i 1 -b 2g -e --trip-times --tos 0 --no-udp-fin > /tmp/tmpexp/client1_stats.txt &
ip netns exec ns0 iperf -c 192.168.11.20 -B 192.168.11.10 -u -p 5011 -t 10 -P 4 -l 1000 -z -i 1 -b 10g -e --trip-times --tos 0 --no-udp-fin > /tmp/tmpexp/client2_stats.txt &
wait
'
: '
# ------------------------------------
# Cleanup
# ------------------------------------

# Detach interfaces from namespaces
ip netns exec ns0 ip link set $INTERFACE0 down
ip netns exec ns1 ip link set $INTERFACE1 down
ip netns exec ns0 ip link set $INTERFACE0 netns 1
ip netns exec ns1 ip link set $INTERFACE1 netns 1

# Delete namespaces
ip netns delete ns0
ip netns delete ns1
'

# ------------------------------------
# Section 4a: If capture was needed for fine-grained analysis
# ------------------------------------
# Convert pcap to csv for analysis using python script
args="-T fields -E header=y -E separator=, \
-e udp.dstport -e frame.time_epoch -e frame.len \
-e iperf.tos -e iperf.id -e iperf.id2 -e iperf.sec -e iperf.usec"
# -e iperf.mport -e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority -e udp.srcport \

# Each flow's tx and rx should be put into {tx1,rx1,tx2,rx2,..}.csv
eval tshark -r /tmp/tmpexp/expt-tx1.pcap $args > /tmp/tmpexp/expt-tx1.csv &
eval tshark -r /tmp/tmpexp/expt-rx1.pcap $args > /tmp/tmpexp/expt-rx1.csv &
eval tshark -r /tmp/tmpexp/expt-tx2.pcap $args > /tmp/tmpexp/expt-tx2.csv &
eval tshark -r /tmp/tmpexp/expt-rx2.pcap $args > /tmp/tmpexp/expt-rx2.csv &
wait
python txrx-analysis.py
# or ./txrx-analysis-rxonly.py

