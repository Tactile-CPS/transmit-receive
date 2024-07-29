#!/bin/bash

# Description   : Generates, transmits and receives packet flows using 2-port NIC on same end-host
# Author        : Joydeep Pal
# Date          : Nov-2022
# Date Modified : 10-Jan-2023, 18-May-2023, 06-Dec-2023 (Overhaul), 05-Jun-2024 (Overhaul)

# System Design:
#
# Port 1 --> || --> Port 2
#
# Each interface is assigned to a network namespace. This is useful when iperf/ping commands
# are to be used on Tx and Rx ports in the same host. Otherwise these commands don't send packets
# out to the wire because kernel routes it internally. Run in root.
# Any Tx flow should go to another interface, same interface doesn't support both tx and rx.
set -e

# Define interface names
INTERFACE1="enp4s0f0"
INTERFACE2="enp4s0f1"

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

# If arp doesn't go through for some reason, fill arp cache
ip netns exec ns1 ip neigh add 192.168.1.2 lladdr 90:e2:ba:f4:e0:e5 dev enp4s0f0
ip netns exec ns2 ip neigh add 192.168.1.1 lladdr 90:e2:ba:f4:e0:e4 dev enp4s0f1

COMMENT << HERE
# ------------------------------------
# Section 1a: If capture is needed (optional)
# ------------------------------------
# Capture packets for fine-grained analysis
# Start packet capture individually for each flow at server (rx)
tshark -i $INTERFACE1 -a duration:7 -s 118 -w /tmp/capture-experiment-rx1.pcap &
tshark -i $INTERFACE1 -a duration:7 -s 118 -w /tmp/capture-experiment-tx1.pcap &
HERE

# Start iperf server & iperf client for each flow
ip netns exec ns2 iperf -s -u -p 5001 > server1_stats.txt &
ip netns exec ns2 iperf -s -u -p 5002 > server2_stats.txt &
# ip netns exec ns2 iperf -s -u -B $INTERFACE2 -P 1 -e --histogram --jitter-histograms -i 1 > server1_stats.txt 2>&1 &

ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > client1_stats.txt &
ip netns exec ns1 iperf -c 192.168.1.2 -u -p 5002 -t 10 -i 1 -b 10m -e --trip-times --tos 0 > client2_stats.txt &
#ip netns exec ns1 iperf -c 192.168.1.2 -u -B $INTERFACE1 -p 5002 -t 10 -i 1 -b 10m -P 1 -l 1000 -e --trip-times --tos 0 > client1_stats.txt 2>&1 &
# Wait for iperf to finish
wait

# ----------------------------------------
# Section 2: If VLAN interfaces are needed
# ----------------------------------------
ip netns exec ns1 ip link set $INTERFACE1 up
ip netns exec ns2 ip link set $INTERFACE2 up

ip netns exec ns1 ip link add link enp4s0f0 name enp4s0f0.11 type vlan id 11
ip netns exec ns1 ip link add link enp4s0f0 name enp4s0f0.12 type vlan id 12
ip netns exec ns1 ip addr add 192.168.1.11/24 dev enp4s0f0.11
ip netns exec ns1 ip addr add 192.168.2.12/24 dev enp4s0f0.12
ip netns exec ns1 ip link set enp4s0f0.11 up
ip netns exec ns1 ip link set enp4s0f0.12 up

ip netns exec ns2 ip link add link enp4s0f1 name enp4s0f1.11 type vlan id 11
ip netns exec ns2 ip link add link enp4s0f1 name enp4s0f1.12 type vlan id 12
ip netns exec ns2 ip addr add 192.168.1.21/24 dev enp4s0f1.11
ip netns exec ns2 ip addr add 192.168.2.22/24 dev enp4s0f1.12
ip netns exec ns2 ip link set enp4s0f1.11 up
ip netns exec ns2 ip link set enp4s0f1.12 up

## iperf server and client
ip netns exec ns2 iperf -s -B 192.168.1.21 -u -p 5001
ip netns exec ns2 iperf -s -B 192.168.2.22 -u -p 5002
ip netns exec ns1 iperf -c 192.168.1.21 -B 192.168.1.11 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0
ip netns exec ns1 iperf -c 192.168.2.22 -B 192.168.2.12 -u -p 5002 -t 10 -i 1 -b 10m -e --trip-times --tos 0

# ------------------------------------
# Section 2a: If capture is needed
# ------------------------------------
ip netns exec ns1 tshark -i enp4s0f0.11 -a duration:5 -s 118 -w /tmp/capture-experiment-tx1.pcap &
ip netns exec ns1 tshark -i enp4s0f0.12 -a duration:5 -s 118 -w /tmp/capture-experiment-tx2.pcap &
ip netns exec ns2 tshark -i enp4s0f1.11 -a duration:5 -s 118 -w /tmp/capture-experiment-rx1.pcap &
ip netns exec ns2 tshark -i enp4s0f1.12 -a duration:5 -s 118 -w /tmp/capture-experiment-rx2.pcap &
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

# ------------------------------------
# Section 1b: Open Multiple Terminals
# ------------------------------------
# Commands to run in each terminal
commands=(
  "echo 'Hello from Terminal 1'"
  "echo 'Hello from Terminal 1'"
  "echo 'Hello from Terminal 1'"
  "echo 'Hello from Terminal 1'"
)
#	"sudo ip netns exec ns2 iperf -s -B 192.168.1.21 -u -p 5001"
#	"sudo ip netns exec ns2 iperf -s -B 192.168.2.22 -u -p 5002"
#	"sudo ip netns exec ns1 iperf -c 192.168.1.21 -B 192.168.1.11 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0"
#	"sudo ip netns exec ns1 iperf -c 192.168.2.22 -B 192.168.2.12 -u -p 5002 -t 10 -i 1 -b 10m -e --trip-times --tos 0"

#  "echo 'Hello from Terminal 1'"
#  "ls -l"
#  "date"
#  "ping -c 3 google.com"

# Open a new terminal window for each command
for ((i=0; i<${#commands[@]}; i++))
do
  gnome-terminal --window --title="Terminal $((i+1))" -- bash -c "${commands[i]}; exec bash"
done



echo '=================== Done !! ====================='
echo ' '

