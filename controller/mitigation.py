"""Small OpenFlow adapter, importable without Ryu for ordinary unit tests."""
COOKIE = 0xD005
PRIORITY = 200


def lab_match(source, destination):
    if source not in ("10.0.0.1", "10.0.0.2") or destination != "10.0.0.3":
        raise ValueError("Mitigation must stay inside the fixed lab")
    # Only this client's IPv4 ICMP to the server; ARP and other clients survive.
    return dict(eth_type=0x0800, ip_proto=1, ipv4_src=source, ipv4_dst=destination)


def install_drop(datapath, source, destination, seconds):
    if isinstance(seconds, bool) or not isinstance(seconds, int) or not 1 <= seconds <= 60:
        raise ValueError("Drop duration must be an integer between 1 and 60")
    parser, ofp = datapath.ofproto_parser, datapath.ofproto
    message = parser.OFPFlowMod(
        datapath=datapath, cookie=COOKIE, priority=PRIORITY,
        match=parser.OFPMatch(**lab_match(source, destination)), instructions=[],
        hard_timeout=seconds, flags=ofp.OFPFF_SEND_FLOW_REM)
    datapath.send_msg(message)
    return message


def remove_drop(datapath, source, destination):
    parser, ofp = datapath.ofproto_parser, datapath.ofproto
    message = parser.OFPFlowMod(
        datapath=datapath, cookie=COOKIE, cookie_mask=0xffffffffffffffff,
        command=ofp.OFPFC_DELETE_STRICT, priority=PRIORITY,
        out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
        match=parser.OFPMatch(**lab_match(source, destination)))
    datapath.send_msg(message)
    return message
