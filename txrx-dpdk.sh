#!/bin/bash

# Description	: Packet Generator, Transmitter and Analysis based on DPDK
# Author        : Joydeep Pal
# Date Created  : Nov-2022
# Date Modified : 26-Apr-2024

# Setup for a Intel NIC when the interfaces don't show up
sudo bash
modprobe -rv ixgbe
modprobe -v ixgbe allow_unsupported_sfp=1
# Setup for using DPDK
modprobe vfio-pci
# Setup for using Netronome as normal NIC
## Reload NFP with visible PFs (which loads nic-firmware)
modprobe -r nfp
modprobe nfp nfp_pf_netdev=1

# Setup DPDK hugepages and PCI NIC devices
cd /home/zenlab/Documents/joy/dpdk
./usertools/dpdk-hugepages.py -p 1G --setup 8G
./usertools/dpdk-devbind.py -s
./usertools/dpdk-devbind.py --bind=none     04:00.0 04:00.1
./usertools/dpdk-devbind.py --bind=vfio-pci 04:00.0 04:00.1
./usertools/dpdk-devbind.py --bind=ixgbe    04:00.0 04:00.1

# Setup Pktgen-DPDK txrx on NIC
## Build pktgen
make clean buildlua
## Test
./usr/local/bin/pktgen -l 0,2 -n 4 --proc-type auto -a 04:00.0 -a 04:00.1 --log-level 7 -- -P -m "[2].0" -T -j -f test/hello-world.lua  # Won't work because of core-port mapping
./usr/local/bin/pktgen -l 0-2 -n 4 --proc-type auto -a 04:00.0 -a 04:00.1 --log-level 7 -- -P -m "1.0" -m "2.1" -T -v -f test/hello-world.lua
## Run
cd /home/zenlab/Documents/joy/Pktgen-DPDK
export RTE_SDK=/home/zenlab/Documents/joy/dpdk
export RTE_TARGET=build
./tools/run.py -s default-custom
./tools/run.py default-custom
enable 0 latency
enable 1 latency
enable 0 vlan
enable 1 vlan
page latency
set 0 proto udp
set 1 proto udp
set 0 rate 100
set 1 rate 100
latency 0 rate 1
latency 1 rate 1
set 0 size 64
set 1 size 64
set 0 txburst 4
set 0 rxburst 4
set 1 txburst 4
set 1 rxburst 4
start 0
start 1
stop 0
clr
set 0 txburst 1
set 0 rxburst 1
set 1 txburst 1
set 1 rxburst 1
set 0 txburst 16
set 0 rxburst 16
set 1 txburst 16
set 1 rxburst 16
set 0 txburst 64
set 0 rxburst 64
set 1 txburst 64
set 1 rxburst 64
page stats
set 0 count 1000000
set 0 vlan 5


# Start traffic on VFs
sudo ip netns add ns0
sudo ip netns add ns1
sudo ip netns add ns2
sudo ip netns add ns3

sudo ip link set vf0_0 netns ns0
sudo ip link set vf0_1 netns ns1
sudo ip link set vf0_2 netns ns2
sudo ip link set vf0_3 netns ns3

sudo ip netns exec ns0 ip a add 192.168.10.50/24 dev vf0_0
sudo ip netns exec ns1 ip a add 192.168.10.51/24 dev vf0_1
sudo ip netns exec ns2 ip a add 192.168.10.52/24 dev vf0_2
sudo ip netns exec ns3 ip a add 192.168.10.53/24 dev vf0_3

sudo ip netns exec ns0 ip link set lo up
sudo ip netns exec ns1 ip link set lo up
sudo ip netns exec ns2 ip link set lo up
sudo ip netns exec ns3 ip link set lo up

sudo ip netns exec ns0 ip link set vf0_0 up
sudo ip netns exec ns1 ip link set vf0_1 up
sudo ip netns exec ns2 ip link set vf0_2 up
sudo ip netns exec ns3 ip link set vf0_3 up

## ARP entries
sudo ip netns exec ns0 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev vf0_0
sudo ip netns exec ns1 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev vf0_1
sudo ip netns exec ns2 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev vf0_2
sudo ip netns exec ns3 ip neigh add 192.168.10.20 lladdr 90:e2:ba:f4:e0:e5 dev vf0_3

## Testing - Start Traffic
sudo ip netns exec ns0 iperf -c 192.168.10.10 -B 192.168.10.50 -u -p 5010 -t 5 -l 64 -z -i 1 -b 10g -e --trip-times --no-udp-fin -P 5 &
sudo ip netns exec ns1 iperf -c 192.168.10.10 -B 192.168.10.51 -u -p 5011 -t 5 -l 64 -z -i 1 -b 10g -e --trip-times --no-udp-fin -P 5 &
sudo ip netns exec ns2 iperf -c 192.168.10.10 -B 192.168.10.52 -u -p 5012 -t 5 -l 64 -z -i 1 -b 10g -e --trip-times --no-udp-fin -P 5 &
sudo ip netns exec ns3 iperf -c 192.168.10.10 -B 192.168.10.53 -u -p 5013 -t 5 -l 64 -z -i 1 -b 10g -e --trip-times --no-udp-fin -P 5

## Testing - Start traffic with taskset
taskset -c 3 sudo ip netns exec ns0 iperf -c 192.168.10.20 -u -p 5010 -t 10 -i 1 -b 10g -l 64 -P 5 --no-udp-fin & \
taskset -c 4 sudo ip netns exec ns1 iperf -c 192.168.10.20 -u -p 5010 -t 10 -i 1 -b 10g -l 64 -P 5 --no-udp-fin 
sudo ip netns exec ns0 iperf -c 192.168.10.20 -u -p 5010 -t 20 -i 1 -b 10g -l 64 -P 8 --no-udp-fin & \
sudo ip netns exec ns1 iperf -c 192.168.10.20 -u -p 5010 -t 20 -i 1 -b 10g -l 64 -P 8 --no-udp-fin

## Testing - Live Datarate
sudo ip netns exec ns1 nload -m vf0_1 vf0_2

