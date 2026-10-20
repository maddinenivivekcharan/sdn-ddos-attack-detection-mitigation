"""OpenFlow 1.3 controller for exactly one isolated three-host switch."""
import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from controller.config import load_config
from controller.detection import RateDetector
from controller.mitigation import COOKIE, install_drop


class LabController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = load_config()
        self.detector = RateDetector(self.config["threshold_pps"], self.config["consecutive_samples"])
        self.switches = {}
        self.blocked = set()
        self.monitor = hub.spawn(self.poll)

    def add_flow(self, dp, priority, match, actions, cookie=0):
        parser = dp.ofproto_parser
        instructions = [parser.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, cookie=cookie, priority=priority,
                                    match=match, instructions=instructions))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def connected(self, event):
        dp = event.msg.datapath
        if dp.id != 1:
            self.logger.error("Refusing unexpected datapath %s (expected 1)", dp.id)
            dp.close()
            return
        parser, ofp = dp.ofproto_parser, dp.ofproto
        # Reset state on a fresh lab connection. OVS secure mode has no fallback forwarding.
        for source in self.config["client_ips"]:
            self.detector.reset((dp.id, source))
            self.blocked.discard((dp.id, source))
        dp.send_msg(parser.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE,
                    out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY, match=parser.OFPMatch()))
        self.add_flow(dp, 0, parser.OFPMatch(), [])  # default drop; no packet-in flood
        self.add_flow(dp, 10, parser.OFPMatch(eth_type=0x0806), [parser.OFPActionOutput(ofp.OFPP_FLOOD)])
        for port, ip in enumerate(self.config["client_ips"], 1):
            # Specific permanent counters include the first ping (no learning delay).
            self.add_flow(dp, 100, parser.OFPMatch(in_port=port, eth_type=0x0800,
                          ip_proto=1, ipv4_src=ip, ipv4_dst=self.config["server_ip"]),
                          [parser.OFPActionOutput(3)], cookie=0x100 + port)
        for port, ip in enumerate(self.config["client_ips"] + [self.config["server_ip"]], 1):
            self.add_flow(dp, 20, parser.OFPMatch(eth_type=0x0800, ipv4_dst=ip),
                          [parser.OFPActionOutput(port)])
        self.logger.info("CONNECTED switch=1 fixed forwarding installed; ports c1=1 c2=2 server=3")

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_changed(self, event):
        if event.state == MAIN_DISPATCHER and event.datapath.id == 1:
            self.switches[1] = event.datapath
        elif event.state == DEAD_DISPATCHER:
            if self.switches.get(event.datapath.id) is event.datapath:
                self.switches.pop(event.datapath.id, None)

    def poll(self):
        while True:
            for dp in list(self.switches.values()):
                dp.send_msg(dp.ofproto_parser.OFPFlowStatsRequest(dp))
            hub.sleep(self.config["poll_seconds"])

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def statistics(self, event):
        dp = event.msg.datapath
        now = time.monotonic()
        for flow in event.msg.body:
            if flow.cookie not in (0x101, 0x102) or flow.priority != 100:
                continue
            source = self.config["client_ips"][flow.cookie - 0x101]
            key = (dp.id, source)
            if key in self.blocked:
                continue  # counters freeze under the higher priority drop
            result = self.detector.observe(key, flow.packet_count, now)
            self.logger.info("OBSERVE source=%s packets=%s suspicious=%s reason=%s",
                             source, flow.packet_count, result.suspicious, result.reason)
            if result.suspicious:
                install_drop(dp, source, self.config["server_ip"], self.config["block_seconds"])
                self.blocked.add(key)
                self.logger.info("MITIGATION requested source=%s ICMP-to-server duration=%ss; confirm via ovs-ofctl",
                                 source, self.config["block_seconds"])

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def removed(self, event):
        msg = event.msg
        if msg.cookie == COOKIE:
            source = msg.match.get("ipv4_src")
            key = (msg.datapath.id, source)
            self.blocked.discard(key)
            self.detector.reset(key)
            self.logger.info("RECOVERY drop removed source=%s reason=%s; verify connectivity with ping", source, msg.reason)

    @set_ev_cls(ofp_event.EventOFPErrorMsg, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error(self, event):
        msg = event.msg
        self.logger.error("OPENFLOW ERROR type=%s code=%s; mitigation/forwarding may have failed", msg.type, msg.code)
