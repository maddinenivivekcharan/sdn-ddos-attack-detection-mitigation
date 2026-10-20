#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec .venv-ryu/bin/ryu-manager --ofp-listen-host 127.0.0.1 --ofp-tcp-listen-port 6653 --log-config-file config/logging.conf controller/sdn_controller.py
