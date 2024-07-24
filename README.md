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

## Analysis scripts
- Reads csv files and calculates latency, jitter, packet loss, out-of-order
- `'txrx-analysis-rxonly.py'`
  - Uses iperf data
  - For latency, uses rx capture's epoch time and iperf's tx time 
- `'txrx-analysis.py'`
  - For latency, uses tx and rx capture's epoch time
