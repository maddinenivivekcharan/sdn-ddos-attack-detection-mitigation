# Architecture

One Mininet network contains c1 (10.0.0.1), c2 (10.0.0.2), server
(10.0.0.3), and OVS s1, datapath ID 1. Ports 1, 2, 3 map to these hosts
respectively. There is no NAT, external interface or default route.

1. OVS connects to Ryu on loopback TCP 6653 and negotiates OpenFlow 1.3.
2. SwitchFeatures initializes the dedicated lab table. Default priority 0 drops
   unmatched packets; priority 10 floods ARP; priority 20 routes IPv4 by fixed
   destination. Priority 100 client ICMP rules override these forwarding rules
   and expose separate per-client counters (cookies 0x101 and 0x102).
3. A Ryu hub task sends FlowStatsRequest every two seconds. Replies may be
   multipart; each permanent client flow is processed independently.
4. RateDetector uses cumulative packet counter deltas and monotonic time. First
   samples and counter resets establish a baseline. Exactly 5 pps is normal;
   two consecutive samples above 5 pps identify an educational rate anomaly.
5. A priority 200 drop (cookie 0xd005) matches only that source's IPv4 ICMP to
   the server. Empty instructions produce no output. This is higher priority
   than forwarding; ARP and c2 remain available. It is a temporary restriction,
   not an attack verdict.
6. Counters under an active drop are not evaluated. Hard timeout expiry or
   explicit cookie deletion produces FlowRemoved; the controller clears blocked
   state and establishes a fresh counter baseline. Persistent elevated traffic
   can trigger again. A restart clears state and reinitializes the lab table.
7. The Linux demo inspects switch rules and connectivity to verify the effect;
   logging a FlowMod request alone is not proof of successful mitigation.

The controller never receives every data packet. The switch performs forwarding
and maintains counters, reducing controller load. Default drop avoids packet-in
storms. Configuration and detection have no Ryu dependency; mitigation uses a
small OpenFlow adapter that can be tested with mocks. The Mininet module imports
its Linux dependencies only inside main, allowing source inspection on Windows.

Failure boundaries: OpenFlow errors are logged; there are no retries or barrier
acknowledgement tracking. If a rule installation fails, requested blocked state
may be stale until restart. If FlowRemoved is lost, reset/restart the controller
once traffic has stopped. Timeouts still execute on OVS while Ryu is offline.
Real systems need reconciled switch state, robust acknowledgements, authentication,
multiple signals, capacity planning and false-positive handling.
