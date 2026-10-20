"""Root-only Linux lab. No NAT, physical interfaces, or external traffic targets."""
import argparse
import os
import subprocess
import time
from controller.config import load_config


def remove_rules():
    subprocess.run(["ovs-ofctl", "-O", "OpenFlow13", "del-flows", "s1",
                    "cookie=0xd005/0xffffffffffffffff"], check=True)


def drop_present():
    result = subprocess.run(["ovs-ofctl", "-O", "OpenFlow13", "dump-flows", "s1"],
                            check=True, text=True, capture_output=True)
    return "cookie=0xd005" in result.stdout.lower()


def demo(net, config):
    c1, c2, server = (net.get(name) for name in ("c1", "c2", "server"))
    time.sleep(config["poll_seconds"] * 2)  # wait for initial baseline
    assert net.pingAll() == 0, "Initial connectivity failed: check controller logs"
    print("PASS normal connectivity; starting bounded 10 pps ICMP from c1 for 8 seconds")
    process = c1.popen(["ping", "-n", "-i", "0.1", "-c", "80", "-W", "1", server.IP()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 8
        found = False
        while time.monotonic() < deadline:
            if drop_present():
                found = True
                break
            time.sleep(0.25)
        assert found, "No mitigation observed; use default thresholds and inspect controller log"
        assert net.ping([c1, server], timeout="1") > 0, "c1 was not restricted"
        assert net.ping([c2, server], timeout="1") == 0, "Legitimate client c2 lost connectivity"
        print("PASS mitigation observed and c2 unaffected")
    finally:
        process.terminate()
        process.wait(timeout=5)
    time.sleep(config["block_seconds"] + 2)
    assert not drop_present(), "Automatic recovery failed"
    assert net.pingAll() == 0, "Connectivity did not recover"
    print("PASS timeout recovery")
    # Exercise explicit deletion separately with another bounded burst.
    process = c1.popen(["ping", "-n", "-i", "0.1", "-c", "80", "-W", "1", server.IP()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 8
        while not drop_present():
            assert time.monotonic() < deadline, "Second mitigation not observed"
            time.sleep(0.25)
    finally:
        process.terminate()
        process.wait(timeout=5)
    remove_rules()
    time.sleep(config["poll_seconds"] * 2)
    assert not drop_present(), "Manual removal failed"
    assert net.pingAll() == 0, "Manual recovery failed"
    print("PASS explicit removal and recovery; integration demonstration complete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        parser.error("Run only on Linux as root, using the documented manual sudo command")
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, RemoteController
    from mininet.cli import CLI
    from mininet.log import setLogLevel
    setLogLevel("info")
    config = load_config()
    net = Mininet(controller=None, switch=OVSSwitch, build=False)
    net.addController("controller", controller=RemoteController, ip="127.0.0.1", port=6653)
    switch = net.addSwitch("s1", dpid="0000000000000001", protocols="OpenFlow13", failMode="secure")
    for port, (name, ip) in enumerate(zip(("c1", "c2", "server"),
                                         config["client_ips"] + [config["server_ip"]]), 1):
        host = net.addHost(name, ip=ip + "/24", mac=f"00:00:00:00:00:{port:02x}")
        net.addLink(host, switch, port2=port)
    try:
        net.build()
        net.start()
        if not net.waitConnected(timeout=10):
            raise RuntimeError("Controller unavailable on loopback port 6653")
        if args.demo:
            demo(net, config)
        else:
            print("Commands: pingall; c1 ping -c 3 10.0.0.3; c2 ping -c 3 10.0.0.3; exit")
            CLI(net)
    finally:
        net.stop()


if __name__ == "__main__":
    main()
