# Description
- Script to generate, transmit, receive, and analyse packet flow 

## Generate, transmit and receive scripts
- `'txrx-same-host.sh'`
  - Transmits iperf flows
  - Options provided in script
    - VLAN tagging
    - Packet capture on tx and rx
    - Packet captures on the basis of udp destination port to separate pcaps
    - Which are then converted to csv files
  - Iperf cannot currently handle tx and rx on same port
  - Hence, currently we send 2 flows (ST & BE) on port 1 and receive both on port 2.
  - Uses namespaces to work on the same host

- `'txrx-separate-hosts.sh'`
  - Doesn't need namespaces to work on separate hosts

- For capture of iperf packets with wireshark/tshark, full header should be present. Hence, for iperf, 76+46=122 bytes is the minimum datarate. Use 128 as minimum by giving iperf payload length as 128-46=82 bytes. 46 bytes include Ethernet, VLAN, IPv4, UDP headers. Also, iperf datarate (-b x) is equivalent to x/x+(fcs+preamble+epiogue=24bytes)

## Analysis scripts
- Reads csv files and calculates latency, jitter, packet loss, out-of-order
- `'txrx-analysis-rxonly.py'`
  - Uses iperf data
  - For latency, uses rx capture's epoch time and iperf's tx time 
- `'txrx-analysis.py'`
  - For latency, uses tx and rx capture's epoch time

# Notes
- For utas, datarate = 6.6M, time = 2s using archive-txrx scripts

