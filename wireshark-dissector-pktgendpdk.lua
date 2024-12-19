--
-- Pktgen-DPDK dissector for latency packets of Pktgen-DPDK-v24.05.3
-- Author       : Joydeep Pal
-- Date         : 17-May-2024
--

local pktgen_dpdk_proto = Proto("pktgen_dpdk","Pktgen-DPDK Latency UDP packet")
local pktgen_dpdk_magic1_F = ProtoField.uint64("pktgen_dpdk.magic1", "pktgen_dpdk psuedo-magic number")
local pktgen_dpdk_magic_F = ProtoField.uint32("pktgen_dpdk.magic", "pktgen_dpdk magic number", base.HEX)
local pktgen_dpdk_seq_F = ProtoField.uint32("pktgen_dpdk.id", "pktgen_dpdk sequence")
local pktgen_dpdk_timestamp_F = ProtoField.uint64("pktgen_dpdk.timestamp", "pktgen_dpdk timestamp")

pktgen_dpdk_proto.fields = {
   pktgen_dpdk_magic1_F, pktgen_dpdk_magic_F, pktgen_dpdk_seq_F, pktgen_dpdk_timestamp_F
}

function pktgen_dpdk_proto.dissector(buffer,pinfo,tree)

 local pktgen_dpdk_magic1_range = buffer(0,6)
 local pktgen_dpdk_magic_range = buffer(6,4)
 local pktgen_dpdk_seq_range = buffer(10,4)
 local pktgen_dpdk_timestamp_range = buffer(14,8)

 local pktgen_dpdk_magic1 = pktgen_dpdk_magic1_range:uint64()
 local pktgen_dpdk_magic = pktgen_dpdk_magic_range:le_uint()
 local pktgen_dpdk_seq = pktgen_dpdk_seq_range:le_uint()
 local pktgen_dpdk_timestamp = pktgen_dpdk_timestamp_range:le_uint64()

 -- Work out the timestamp from the sec and usec
 -- local timestamp = (pktgen_dpdk_sec * 1.0) + (pktgen_dpdk_usec / 1000000.0)
 -- local pktgen_dpdk_time = format_date(timestamp)

 local subtree = tree:add(pktgen_dpdk_proto, buffer(0,22), "pktgen_dpdk packet data")
 subtree:add(pktgen_dpdk_magic1_F, pktgen_dpdk_magic1_range, pktgen_dpdk_magic1)
 subtree:add(pktgen_dpdk_magic_F, pktgen_dpdk_magic_range, pktgen_dpdk_magic)
 subtree:add(pktgen_dpdk_seq_F, pktgen_dpdk_seq_range, pktgen_dpdk_seq)
 subtree:add(pktgen_dpdk_timestamp_F, pktgen_dpdk_timestamp_range, pktgen_dpdk_timestamp)

Dissector.get("data"):call(buffer(22,buffer:len()-22):tvb(), pinfo, tree)
end
DissectorTable.get("udp.port"):add("1000-9999", pktgen_dpdk_proto)
