void pktgen_page_display(void);

void pktgen_packet_ctor(port_info_t *info, int32_t seq_idx, int32_t type);
void pktgen_packet_rate(port_info_t *info); - Calculate the number of cycles to wait between sending bursts of traffic/ Calculate the transmit rate.
	pps = rate / wire_size
	cycles per burst = example (40 cycles per burst of 4 packets)
	port->tx_cycles = 40 * Number of Tx queues (say 1000 packets)  - Number cycles between TX burst
uint64_t pktgen_wire_size(pinfo); - Calculate the wire size of the data in bits to be sent./ Calculate the number of bytes/bits in a burst of traffic. / RETURNS: Number of bytes in a burst of packets. (Written wrongly, it is bits)
	(uint64_t)(pkt_size(=64-4) + INTER_FRAME_GAP + START_FRAME_DELIMITER + PKT_PREAMBLE_SIZE + RTE_ETHER_CRC_LEN(12+7+1+4)) *8 = bits

int pktgen_find_matching_ipsrc(port_info_t *info, uint32_t addr);
int pktgen_find_matching_ipdst(port_info_t *info, uint32_t addr);

int pktgen_launch_one_lcore(void *arg);
uint64_t pktgen_wire_size(port_info_t *info);
void pktgen_input_start(void);
void stat_timer_dump(void);
void stat_timer_clear(void);
void pktgen_timer_setup(void);
double next_poisson_time(double rateParameter);

uint64_t pktgen_get_time(void)
uint64_t pktgen_get_timer_hz(void)
pktgen_set_port_flags
pktgen_clr_port_flags
pktgen_tst_port_flags
pktgen_tst_port_flags
pktgen_clr_q_flags
pktgen_tst_q_flags

do_command


pktgen.c
pktgen_fill_pattern()
pktgen_tstamp_pointer()
pktgen_tstamp_inject()
	pkt_seq_t *pkt = &pinfo->seq_pkt[LATENCY_PKT];
	Get the structure of port latency metrics
	if time > latency-injection-time-interval
		pktsize = mbuf->pkt_len = mbuf->data_len = pkt->pkt_size
		pktgen_packet_ctor(pinfo, LATENCY_PKT, -2); ## IPv4 Packet Construction
		rte_eth_tx_burst(pinfo->pid, qid, &mbuf, to_send);  # send only (to_send=1) 1 packet
pktgen_packet_ctor(port_info_t *pinfo, int32_t seq_idx, int32_t type)
	pkt_seq_t *pkt            = &pinfo->seq_pkt[seq_idx];
	if (seq_idx == LATENCY_PKT) {
		tstamp = pktgen_tstamp_pointer(info, (char *)&pkt->hdr);
	l3_hdr = pktgen_ether_hdr_ctor(info, pkt);
	pktgen_udp_hdr_ctor(pkt, l3_hdr, RTE_ETHER_TYPE_IPV4);
	pktgen_ipv4_ctor(pkt, l3_hdr);
		
	}
	
pktgen_validate_pkt() if TX_DEBUG defined
tx_send_packets()
	rte_eth_tx_burst(pinfo, qid, pkts, txCnt) ## Send a burst of output packets on a transmit queue of an Ethernet device. Send thos txCnt packets
	if qid=0 & pktgen_tst_port_flags(pinfo, SEND_LATENCY_PKTS)) # if queue id is 0, only then do this, why? 
		pktgen_tstamp_inject(pinfo, qid);
Removed -> pktgen_do_tx_tap()
Removed -> pktgen_send_burst()
			
Removed -> pktgen_tx_flush()
pktgen_exit_cleanup()

pktgen_has_work()
pktgen_packet_type()
pktgen_packet_classify()
pktgen_packet_classify_bulk()
pktgen_send_special()
Removed -> pktgen_setup_cb()
pktgen_setup_packets(pid)
	if (pktgen_tst_port_flags(pinfo, SETUP_TRANSMIT_PKTS)) {
		struct pkt_setup_s s;
		int32_t idx = SINGLE_PKT;
		s.seq_idx = idx;
		pktgen_clr_port_flags(pinfo, SETUP_TRANSMIT_PKTS);
pktgen_send_pkts()
	define txCnt and mbuf array[burstsize];
	define rte_mbuf array *pkts[] with input as "pinfo->tx_burst" packets
	txCnt = pkt_atomic64_tx_count(&pinfo->current_tx_count, pinfo->tx_burst);
		- if txCnt > burst, txCnt = burst
	tx_send_packets(pinfo, qid, pkts, txCnt);
port_map_info()

pktgen_main_transmit(*pinfo, uint16_t qid)
	if SEND_ARP_PING_REQUESTS -> pktgen_send_special()
	if pktgen_tst_port_flags -> SENDING_PACKETS
		mp = l2p_get_tx_mp(pinfo->pid);
		void pktgen_setup_packets(pinfo->pid)
		pinfo->qcnt[qid]++;
		pktgen_send_pkts(pinfo, qid, mp); /* Transmit a set of packets mbufs to a given port. */
Removed ->	if pktgen_tst_q_flags = DO_TX_FLUSH -> pktgen_tx_flush(info, qid);

pktgen_main_receive(port_info_t *pinfo, uint16_t qid, struct rte_mbuf **pkts_burst, uint16_t nb_pkts)
	nb_rx = rte_eth_rx_burst(pid, qid, pkts_burst, nb_pkts)
	struct rte_eth_stats *qstats = &pinfo->queue_stats;
	update stats
	pktgen_tstamp_check(port_info_t *pinfo, struct rte_mbuf **pkts, uint16_t nb_pkt) (pinfo, pkts_burst, nb_rx)
		get lcore id, rxqueue id, port_info->latency struct
		for 0,nb_pkts
			if (pktgen_tst_port_flags(pinfo, SEND_LATENCY_PKTS)) {
				pktgen_tstamp_pointer()
				measure latency using packet timestamp and current timestamp
				match tstamp_magic, and increment counter latncy packet count
				if (pktgen_tst_port_flags(pinfo, SEND_LATENCY_PKTS)) { ????
					calculate latency, jitter stats
				if (pktgen_tst_port_flags(pinfo, SAMPLING_LATENCIES)
					latsamp_stats_t *stats = &pinfo->latsamp_stats[rx qid];
	pktgen_packet_classify_bulk(pkts_burst, nb_rx, pid, qid);
	if CAPTURE_PKTS -> pktgen_packet_capture_bulk(pkts_burst, nb_rx, capture);
	rte_pktmbuf_free_bulk(pkts_burst, nb_rx);
					
		
## main tx/rx loops code - continues until you quit it
pktgen_main_rxtx_loop()
	struct rte_mbuf *pkts_burst[MAX_PKT_RX_BURST];
	uint16_t rx_qid, tx_qid;
	pktgen_main_receive(pinfo, rx_qid, pkts_burst, pinfo->tx_burst);
	pktgen.tx_next_cycle = curr_tsc + pinfo->tx_cycles (old - pmap.tx.infos[0]->tx_cycles;)
	/* Determine when is the next time to send packets */
	pktgen_main_transmit(pinfo, tx_qid)   -> If Multi-queue, then what happens?
pktgen_main_tx_loop()
	uint16_t tx_qid;
	tx_next_cycle = curr_tsc + pinfo->tx_cycles;
	/* Determine when is the next time to send packets */
	pktgen_main_transmit()
pktgen_main_rx_loop()
	struct rte_mbuf *pkts_burst[MAX_PKT_RX_BURST];
	uint16_t rx_qid;
	pktgen_main_receive(pinfo, rx_qid, pkts_burst, pinfo->tx_burst)

enum { LATSAMPLER_UNSPEC, LATSAMPLER_SIMPLE, LATSAMPLER_POISSON };
removed -> struct pkt_data_t {port_info_t *info; uint16_t qid;}


# Main - pktgen-main.h & .c
void pktgen_l2p_dump(void);
void pktgen_interact(void);
void *pktgen_get_lua(void);
void pktgen_stop_running(void);
pktgen_launch_one_lcore()
pktgen_parse_args()

main()
	pktgen_parse_args()
	void pktgen_config_ports(void)
		struct rte_eth_conf, pid, pkt_seq_t *pkt, port_info_t *pinfo, l2p_port_t *port;
		
	pktgen_launch_one_lcore()
		get coremap if RXTYPE pktgen_main_rx_loop(lid);
			if TXTYPE pktgen_main_tx_loop(lid);
			if (RXTYPE|TXTYPE) pktgen_main_rxtx_loop(lid);

Notes :
- By default rate is 10G NIC and 100%.
- When setting rate percentage using 'set 0 rate 1', single_set_tx_rate() is called which in turn calls pktgen_packet_rate()
	

# DPDK codebase
rte_eth_tx_burst() -> https://github.com/DPDK/dpdk/blob/main/lib/ethdev/rte_ethdev.h#L6347
	nb_pkts = p->tx_pkt_burst(qd, tx_pkts, nb_pkts);
	rte_ethdev_trace_tx_burst(port_id, queue_id, (void **)tx_pkts, nb_pkts);
	return nb_pkts;
}
