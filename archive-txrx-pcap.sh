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
#ssh zenlab@10.114.64.114  # tx
#ssh -X zenlab@10.114.64.114  # rx
#ssh zenlab@10.114.64.194  # nfp

# Provide permissions to networking tools (one-time)
#sudo chmod +x /usr/bin/dumpcap

# --------
# Setup
# --------
# tx
#cd ~/Documents/archive-pcap-txrx/vlan-pcap-files
# rx
# one-time
#sudo modprobe -rv ixgbe
#sudo modprobe -v ixgbe allow_unsupported_sfp=1
# make tmp directory to store new experiment csv files
#mkdir /tmp/tmpexp

# -------------------
# tx system
# -------------------
# capture
sudo echo hello
tshark -i enp4s0f1 -f "vlan and udp dst port 5001" -a duration:10 -s 128 -w /tmp/tmpexp/expt-tx1.pcap &
tshark -i enp4s0f1 -f "vlan and udp dst port 5002" -a duration:10 -s 128 -w /tmp/tmpexp/expt-tx2.pcap &
sleep 2
# transmit
sudo tcpreplay -i enp4s0f1 -M 50m --duration=5 Traffic_Flow_vlan_10_packetsize_128B_priority_0__NoPrio_dev.pcap &
sudo tcpreplay -i enp4s0f1 -M 50m --duration=5 Traffic_Flow_vlan_11_packetsize_128B_priority_0__NoPrio_dev.pcap &
wait
# pcap to csv and transfer
args="-T fields -E header=y -E separator=, \
-e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority \
-e udp.srcport -e udp.dstport -e frame.time_epoch -e frame.len"
tshark -r /tmp/expt-tx1.pcap $args > /tmp/expt-tx1.csv &
tshark -r /tmp/expt-tx2.pcap $args > /tmp/expt-tx2.csv &
wait
scp /tmp/expt-tx1.csv zenlab@10.114.64.114:/tmp/tmpexp/
scp /tmp/expt-tx2.csv zenlab@10.114.64.114:/tmp/tmpexp/

# -------------------
# rx system
# -------------------
# capture
tshark -i enp4s0f0 -f "vlan and udp dst port 5001" -a duration:10 -s 128 -w /tmp/tmpexp/expt-rx1.pcap &
tshark -i enp4s0f0 -f "vlan and udp dst port 5002" -a duration:10 -s 128 -w /tmp/tmpexp/expt-rx2.pcap &
wait
sleep 2
# pcap to csv and store
args="-T fields -E header=y -E separator=, \
-e udp.dstport -e frame.time_epoch -e frame.len \
-e iperf.tos -e iperf.id -e iperf.id2 -e iperf.sec -e iperf.usec"
# -e iperf.mport -e ip.src -e ip.dst -e ip.id -e vlan.id -e vlan.priority -e udp.srcport \
tshark -r /tmp/tmpexp/expt-rx1.pcap $args > /tmp/tmpexp/expt-rx1.csv &
tshark -r /tmp/tmpexp/expt-rx2.pcap $args > /tmp/tmpexp/expt-rx2.csv &
wait
# verify capture
ls -al /tmp/tmpexp
# analysis
python ../archive-analysis.py

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

