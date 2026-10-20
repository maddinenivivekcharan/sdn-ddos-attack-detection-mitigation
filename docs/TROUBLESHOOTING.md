# Troubleshooting

| Symptom | Check and action |
|---|---|
| Windows Python opens Store | Use a real Python installation or the existing workspace runtime in README. |
| Cannot import controller during tests | Run from project root with `python run_tests.py`. This also handles embeddable Python path isolation. |
| Mininet missing | On Linux check `/usr/bin/python3 -c 'import mininet'`; Mininet is an OS package, not in the controller venv. |
| ALREADY_HANDLED import error | Use CPython 3.8 and pinned requirements in a fresh venv; Eventlet 0.30.3+ removed Ryu 4.34's required API. |
| TimeoutError immutable type error | Old Eventlet cannot run under newer Python. Do not use Python 3.10+ for this controller. |
| setuptools easy_install/get_script_args error | Recreate venv and install setuptools 57.5.0 before Ryu. Avoid a global downgrade. |
| OVS database connection fails | Check `systemctl status openvswitch-switch`. Start the service manually as described in README. |
| ovs kernel module missing | Use a Linux VM with OVS datapath support. WSL kernel/modules may be unsuitable for this topology. |
| Controller not connected | Start controller first; inspect log; check `ss -ltn` for loopback 6653. Ensure OpenFlow13 and dpid 1. |
| pingall fails | Wait a few seconds, inspect flows using `sudo ovs-ofctl -O OpenFlow13 dump-flows s1`; port mapping must be 1/2/3. |
| Demo never detects | Use default config and inspect OBSERVE logs; confirm ICMP counters and scheduling. The burst is bounded; do not increase flood volume. |
| No logs or invalid logging path | Start using the provided script from the project; it creates logs/ and sets the working directory. |
| c1 remains restricted | Stop its traffic, wait 10 seconds, inspect drop cookie; manually run reset script. Ongoing traffic can trigger again. |
| Controller says blocked but no drop exists | Check OpenFlow errors/lost FlowRemoved; stop traffic and restart the controller in this dedicated lab. |
| Stale bridge after crash | Close lab processes. In the dedicated VM only, manually use `sudo mn -c`; this affects all Mininet labs. |
| Permission denied on a shell script | Use `bash scripts/...sh`; executable mode is not required. Scripts use LF through .gitattributes. |

Do not disable firewalls broadly or attach s1 to an Internet-facing interface.
Do not install the legacy controller packages in your system Python. Preserve
actual failure messages when documenting integration results; expected output is
not evidence of a successful run.
