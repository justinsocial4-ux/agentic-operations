#!/bin/sh
# Loopback-only launcher for the Presales Deal & Capacity Orchestrator review UI.
#
# Recommendation-only prototype. No credentials, no live vendor calls, no remote
# LLM, no writes. The fictional demo and the authorized-import path require no
# network access. This launcher:
#   - resolves package-relative paths;
#   - binds loopback (127.0.0.1) only;
#   - never reads ambient credentials or proxies (Streamlit config sets
#     gatherUsageStats=false and the transport uses trust_env=False);
#   - prints bounded remediation on a missing toolchain or busy port.
#
# Usage:
#   ./run_demo.sh                                 # fictional demo on 127.0.0.1:8501
#   ./run_demo.sh --mode import --headless --port 8501
#   ./run_demo.sh --mode connect --port 8501
#   ./run_demo.sh --network-disabled             # explicit no-network fictional/import
#
# --mode {demo|import|connect} is informational: all three start paths are
# always available on the single landing page. connect is optional and remains
# the contract-tested read-only adapter path; file import is the fallback.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

MODE="demo"
PORT="8501"
HEADLESS="true"
NETWORK_DISABLED="0"

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:-demo}"; shift 2 ;;
    --mode=*) MODE="${1#*=}"; shift ;;
    --port) PORT="${2:-8501}"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --headless) HEADLESS="true"; shift ;;
    --no-headless) HEADLESS="false"; shift ;;
    --network-disabled) NETWORK_DISABLED="1"; shift ;;
    -h|--help)
      sed -n '2,25p' "$0"
      exit 0 ;;
    *) printf '%s\n' "Unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

case "$MODE" in
  demo|import|connect) : ;;
  *) printf '%s\n' "Invalid --mode '$MODE' (use demo|import|connect)" >&2; exit 2 ;;
esac

if ! command -v uv >/dev/null 2>&1; then
  cat >&2 <<'REMEDIATION'
uv was not found on PATH.
Install it (https://docs.astral.sh/uv/) then re-run:
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ./run_demo.sh
REMEDIATION
  exit 3
fi

printf '%s\n' "Start mode: $MODE (all start paths are available on the landing page)."
if [ "$NETWORK_DISABLED" = "1" ]; then
  printf '%s\n' "Network-disabled: the fictional and import paths need no network access."
fi
printf '%s\n' "Serving loopback only at http://127.0.0.1:$PORT"
printf '%s\n' "Press Ctrl+C to stop. No account, key, or model is required for the demo."

# --frozen keeps the pinned lock; the .streamlit/config.toml pins loopback,
# headless, and telemetry-off. trust_env=False in the transport blocks ambient
# proxy/credential inheritance.
exec uv run --frozen streamlit run src/orchestrator/ui/app.py \
  --server.address 127.0.0.1 \
  --server.port "$PORT" \
  --server.headless "$HEADLESS" \
  --browser.gatherUsageStats false
