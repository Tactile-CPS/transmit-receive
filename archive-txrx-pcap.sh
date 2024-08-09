#!/bin/bash

# -------------------------------------------------------
# Description 	: Transmits saved pcaps
# Author        : Joydeep Pal
# Date          : 26-Jul-2024
# -------------------------------------------------------

# -------------------------------------------------------
# Details:
# Helpful in testing old uTAS-like programs which don't have capability to forward arp/ping etc.
# System Design: Tx and Rx on any port
# Flows are defined using VLAN IDs
# Uses python script to analyze pcaps and generate plots to demonstrate performance
# -------------------------------------------------------

# Systems used: ssh details
ssh zenlab@10.114.64.114  # tx
ssh -X zenlab@10.114.64.114  # rx
ssh zenlab@10.114.64.194  # nfp

# Provide permissions to networking tools (one-time)
sudo chmod +x /usr/bin/dumpcap

# --------
# Setup
# --------
# tx
cd ~/Documents/archive-pcap-txrx/vlan-pcap-files
# rx
# one-time
sudo modprobe -rv ixgbe
sudo modprobe -v ixgbe allow_unsupported_sfp=1
# make tmp directory to store new experiment csv files
mkdir /tmp/tmpexp

# -------------------
# tx system
# -------------------
# capture
sudo echo hello
tshark -i enp4s0f0 -f "vlan and udp dst port 3002" -a duration:7 -s 118 -w /tmp/expt-utas-tx1.pcap &
tshark -i enp4s0f0 -f "vlan and udp dst port 3003" -a duration:7 -s 118 -w /tmp/expt-utas-tx2.pcap &
sleep 2
# transmit
sudo tcpreplay -i enp4s0f0 -M 400M --duration=10 Traffic_Flow_vlan\(2\)_packetsize\(100B\)_Priority\(0\)_NoPrio_dev.pcap &
sudo tcpreplay -i enp4s0f0 -M 400M --duration=10 Traffic_Flow_vlan\(3\)_packetsize\(100B\)_Priority\(0\)_NoPrio_dev.pcap
# pcap to csv and transfer
args="-T fields -E header=y -E separator=, \
-e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority \
-e udp.srcport -e udp.dstport -e frame.time_epoch -e frame.len"
tshark -r /tmp/expt-utas-tx1.pcap $args > /tmp/expt-utas-tx1.csv &
tshark -r /tmp/expt-utas-tx2.pcap $args > /tmp/expt-utas-tx2.csv &
wait
scp /tmp/expt-utas-tx1.csv zenlab@10.114.64.114:/tmp/tmpexp/
scp /tmp/expt-utas-tx2.csv zenlab@10.114.64.114:/tmp/tmpexp/

#--------------------
# rx system
# -------------------
# capture
tshark -i enp4s0f1 -f "vlan and udp dst port 3002" -a duration:7 -s 118 -w /tmp/expt-utas-rx1.pcap &
tshark -i enp4s0f1 -f "vlan and udp dst port 3003" -a duration:7 -s 118 -w /tmp/expt-utas-rx2.pcap &
wait
sleep 1
# pcap to csv and store
args="-T fields -E header=y -E separator=, \
-e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority \
-e udp.srcport -e udp.dstport -e frame.time_epoch -e frame.len"
tshark -r /tmp/expt-utas-rx1.pcap $args > /tmp/tmpexp/expt-utas-rx1.csv &
tshark -r /tmp/expt-utas-rx2.pcap $args > /tmp/tmpexp/expt-utas-rx2.csv &
wait
# verify capture
ls -al /tmp/tmpexp
# analysis
../archive-analysis.py

#--------------------
# nfp system
# -------------------
# To test basic-forwarding
cd ~/Documents/joy/nfp-experiments/nfp-codes/main_template_build || exit
./p4-development-setup.sh build-C
# Change experiment name and rerun above command
cd ~/Documents/joy/nfp-experiments/experiments/exp-4-tas
./tsn-configure-queues.sh

# ptp
cd /home/zenlab/linuxptp/configs
sudo ethtool -K enp1s0f0 tx off
sudo ethtool -K enp1s0f0 rx off
sudo ip a add 10.0.0.1/24 dev enp1s0f0
ptp4l -i enp1s0f0 -m
phc2sys -s enp1s0f0 -c CLOCK_REALTIME -w -m &

cd /home/zenlab/Documents/time-sync/ptp/linuxptp/configs
sudo ip a add 10.0.0.2/24 dev enp4s0f0
ptp4l -i enp4s0f0 -f default.cfg -m &
phc2sys -c CLOCK_REALTIME -d enp4s0f0 -w -m &

echo 'Done !!'
echo ' '
