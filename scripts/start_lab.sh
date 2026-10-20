#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $EUID -ne 0 ]]; then echo "Manually run: sudo bash scripts/start_lab.sh [--demo]"; exit 1; fi
exec /usr/bin/python3 -m topology.mininet_topology "$@"
