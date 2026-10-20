#!/usr/bin/env bash
set -euo pipefail
# Removes only this application's mitigation cookie on the fixed lab bridge.
if [[ $EUID -ne 0 ]]; then echo "Manually run: sudo bash scripts/reset_lab.sh"; exit 1; fi
exec ovs-ofctl -O OpenFlow13 del-flows s1 'cookie=0xd005/0xffffffffffffffff'
