# Interview guide

## A short introduction

?I built a defensive SDN lab where a controller monitors simulated traffic and
programs a virtual switch to temporarily restrict an unusual ICMP source. I
separated portable tests from Linux network integration so I can explain exactly
what I verified.?

## Explain the architecture

Two Mininet clients and a server connect to one Open vSwitch. Ryu communicates
with the switch using OpenFlow 1.3. OVS forwards packets; Ryu polls counters and
makes decisions. The detector calculates packets per second from counter changes.
Two elevated samples cause a temporary drop rule for one source and destination.
The other client remains connected. A hard timeout or manual deletion restores
access, and pings verify recovery.

## Example scenario

Normal traffic is a few pings. The demonstration sends at most 80 pings at 10 per
second from c1, not a flood. With the default 5 pps educational threshold, two
elevated observations should trigger mitigation. c2 can still reach the server.
Do not say this traffic proves an attack or claim live results before running the
Linux demonstration yourself.

## Questions and simple answers

- **What is DDoS?** Multiple sources overwhelm a service. This lab demonstrates
  rate monitoring and mitigation mechanics, not a full distributed attack.
- **What is SDN?** Control software programs how switches forward traffic.
- **What does Mininet do?** Creates simulated hosts and links using Linux namespaces.
- **What does OVS do?** Forwards traffic and applies OpenFlow rules.
- **What does Ryu do?** Reads counters, runs detection and installs temporary rules.
- **What is OpenFlow?** The protocol between controller and switch.
- **Why two samples?** To avoid reacting to a single brief spike; false positives
  are still possible.
- **Why counter deltas?** Total packets only grow; changes over elapsed time give
  the recent average rate.
- **Why priority 200?** It overrides priority 100 ICMP forwarding for the matching
  source only. Priority is compared among matching rules.
- **How is recovery safe?** The switch expires the rule, even without Ryu. We
  also provide explicit cookie-based deletion and test reachability afterward.
- **Does it block all traffic?** Only IPv4 ICMP from the flagged client to the
  server. Other clients, ARP and other IP protocols are outside the drop match.
- **What did you test on Windows?** Configuration, deterministic counter samples,
  rule message fields and recovery logic with unittest. Real OVS behavior needs Linux.
- **What would production need?** Supported dependencies, several traffic signals,
  source validation, reconciled flow state, TLS, tuning and false-positive review.
- **How does this help IT support?** It practices IP addressing, connectivity
  checks, service/dependency troubleshooting, logs and explaining evidence clearly.

Be candid about limitations. Describe the project as a completed implementation
with tested portable logic and separately verifiable Linux integration, until
you have recorded a real successful integration run.
