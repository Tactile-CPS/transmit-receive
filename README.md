# Description: This folder consists of scripts 
#### Date: 08-May-2023
1. for generating packets (generate-vlan-flows)
2. transmit from source, save packet capture as pcap at receiver, convert pcap to csv, analyse csv

	- 'pcap' and 'csv' files are stored in '${PROJECT_FOLDER}/data-pcap-csv' folder
	- Plots are in '${PROJECT_FOLDER}/Results' folder

## Packet generation scripts are in 'generate-vlan-flows' directory
	
	- generate-custom-vlan-tagged-packets-for-metadata.py: Generate packets with a custom Metadata Header of 40 Bytes (5 fields of 8 bytes) with distinct default values
	- generate-vlan-tagged-packets-individual-v7-multiprocessing.py: Generate multiple distinct traffic flows with uniquely identifiable packets. Uses VLAN IDs, priority (PCP field of VLAN header) and UDP destination ports for identification. Uses multiple CPU cores to generate flows parallely.

### Generated packet flows are stored in "Documents/vlan-pcap-files/"
1. Created [07 May 2023] - Generate 5 packets with a Metadata Header of 40 Bytes for testing reading pcap files, filtering and extracting information

	- Traffic_Flow_vlan(2)_packetsize(500B)_Priority(0)_NoPrio_metadata_test11.pcap
	- Traffic_Flow_vlan(2)_packetsize(1000B)_Priority(0)_NoPrio_metadata_test11.pcap

2. Created [07 May 2023]

	- Traffic_Flow_vlan(2)_packetsize(1000B)_Priority(0)_NoPrio_metadata_test10.pcap
	- Traffic_Flow_vlan(2)_packetsize(500B)_Priority(0)_NoPrio_metadata_test10.pcap

## These directories consists of Packet transmission scripts and analysis scripts

### 'vlan-transmit'
- Transmits VLAN flows at a specified rate for a specified duration or packet count
	- [21 Aug 2023] exp-vlan-transmit-v4.sh
- Analyses latency, packet loss for each VLAN flow by reading tx and rx pcaps
	- [21 Aug 2023] latency-v6.py

### 'metadata-capture'
- Transmits VLAN flows with custom Metadata header at a specified rate for a specified packet count, converts to csv. Packet Processing done in NFP, adds timestamps to Metadata Header.
	- [25 Aug 2023] exp-metadata-capture-transmit.sh, 
- Analyses latency from timestamps in the Metadata header by reading tx and rx pcaps
	- [25 Aug 2023] metadata-capture-analyse-pcap.py

## Results  - Without sync
	- [05 May 2023] Test2_sync_error - 01hr 10pps, falls 24ms
	- [07 May 2023] Test2_sync_error - 03hr 01pps, falls 60ms
	- [08 May 2023] Test2_sync_error - 15min 1pps, falls 04ms 
## Results - With sync

