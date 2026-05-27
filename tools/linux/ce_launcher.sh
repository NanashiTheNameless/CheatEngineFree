#!/usr/bin/env bash
set -euo pipefail
CE_BIN="$1"
shift || true

UID_TO_BLOCK="$(id -u)"
ORIG_USER_NAME="$(logname 2>/dev/null || echo "${SUDO_USER:-${USER:-$(id -un)}}")"
if [ "${ORIG_USER_NAME:-}" = "root" ]; then
  echo "Refusing to run Cheat Engine as root. Run the launcher as a regular user so Cheat Engine runs unprivileged." >&2
  exit 1
fi
DISPLAY_VAL="${DISPLAY:-}"
XAUTH_VAL="${XAUTHORITY:-}"
SUDO_HELPER=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v pkexec >/dev/null 2>&1; then
    SUDO_HELPER=pkexec
  elif command -v sudo >/dev/null 2>&1; then
    SUDO_HELPER=sudo
  else
    SUDO_HELPER=""
  fi
fi

create_and_run_wrapper() {
  mode="$1"; shift
  tmpdir=$(mktemp -d /tmp/ce-block-XXXXXX)
  pidfile="$tmpdir/pid"
  readyfile="$tmpdir/ready"
  helper=$(mktemp /tmp/ce-helper-XXXXXX.sh)
  cat > "$helper" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
TARGET_UID="$1"; shift
PIDFILE="$1"; shift
READYFILE="$1"; shift
MODE="$1"; shift
if [ "$MODE" = "nft" ]; then
  nft add table inet ce_block 2>/dev/null || true
  nft 'add chain inet ce_block output { type filter hook output priority 0 ; }' 2>/dev/null || true
  nft add rule inet ce_block output meta skuid "$TARGET_UID" drop
elif [ "$MODE" = "iptables" ]; then
  iptables -I OUTPUT -m owner --uid-owner "$TARGET_UID" -j REJECT
else
  echo "unknown mode" >&2
  exit 2
fi
touch "$READYFILE"
while [ ! -f "$PIDFILE" ]; do
  sleep 0.1
done
TARGET_PID=$(cat "$PIDFILE")
while kill -0 "$TARGET_PID" 2>/dev/null; do
  sleep 0.5
done
if [ "$MODE" = "nft" ]; then
  nft delete table inet ce_block 2>/dev/null || true
elif [ "$MODE" = "iptables" ]; then
  iptables -D OUTPUT -m owner --uid-owner "$TARGET_UID" -j REJECT 2>/dev/null || true
fi
rm -f "$READYFILE" "$PIDFILE" "$0"
exit 0
EOS
  chmod +x "$helper"
  if [ -n "$SUDO_HELPER" ]; then
    if [ "$SUDO_HELPER" = "pkexec" ]; then
      pkexec "$helper" "$UID_TO_BLOCK" "$pidfile" "$readyfile" "$mode" &
    else
      sudo "$helper" "$UID_TO_BLOCK" "$pidfile" "$readyfile" "$mode" &
    fi
  else
    "$helper" "$UID_TO_BLOCK" "$pidfile" "$readyfile" "$mode" &
  fi

  n=0
  while [ ! -f "$readyfile" ] && [ $n -lt 100 ]; do
    sleep 0.1
    n=$((n+1))
  done
  if [ ! -f "$readyfile" ]; then
    echo "Failed to install network rule" >&2
    rm -rf "$tmpdir"
    exit 2
  fi

  "$CE_BIN" "$@" &
  CE_PID=$!
  echo "$CE_PID" > "$pidfile"
  wait "$CE_PID"
  rm -rf "$tmpdir"
}

if command -v nft >/dev/null 2>&1; then
  create_and_run_wrapper nft "$@"
  exit $?
fi

if command -v iptables >/dev/null 2>&1; then
  create_and_run_wrapper iptables "$@"
  exit $?
fi

echo "Cannot enforce network-only isolation: nft/iptables not available." >&2
echo "Options: install nftables/iptables and run with appropriate privileges (pkexec/sudo)." >&2
exit 1
