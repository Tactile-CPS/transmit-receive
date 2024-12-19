# Define interface names
INTERFACE1="vf0_0"

ip addr add 192.168.1.1/24 ev $INTERFACE1

# If arp doesn't go through for some reason, fill arp cache
ip neigh add 192.168.1.2 lladdr 90:e2:ba:f4:e0:e5 dev $INTERFACE1

iperf -c 192.168.1.2 -u -p 5001 -t 10 -i 1 -b 10m -e --trip-times --tos 0
