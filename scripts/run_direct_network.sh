#!/usr/bin/env bash
# Run a command with Cursor sandbox HTTP proxies unset (direct egress).
# Usage: ./scripts/run_direct_network.sh uv run python scripts/build_training_events.py
set -euo pipefail
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy \
  GIT_HTTP_PROXY GIT_HTTPS_PROXY SOCKS_PROXY SOCKS5_PROXY \
  socks_proxy socks5_proxy || true
export NO_PROXY='*'
export no_proxy='*'
exec "$@"
