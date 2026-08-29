#!/usr/bin/env bash
# Intentionally no `set -e`: update checks must never block the agent.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
CONFIG_FILE="$SKILL_DIR/.env"
CHECK_INTERVAL=28800

# Published versions live on the public npm registry; this works for both
# internal and external installs. Silently skip when offline.
NPM_PACKAGE="@bitget-ai/getagent-skill"
DIST_TAGS_URL="https://registry.npmjs.org/-/package/${NPM_PACKAGE}/dist-tags"

read_local_version() {
  if [ ! -f "$SKILL_MD" ]; then
    echo ""
    return
  fi
  sed -n 's/^[[:space:]]*version:[[:space:]]*\(.*\)/\1/p' "$SKILL_MD" 2>/dev/null | head -1
}

last_check=0
if [ -f "$CONFIG_FILE" ]; then
  last_check=$(sed -n 's/^last_check=\(.*\)/\1/p' "$CONFIG_FILE" 2>/dev/null | head -1 || echo "0")
  last_check=${last_check:-0}
fi

now=$(date +%s 2>/dev/null || echo "0")
elapsed=$((now - last_check)) 2>/dev/null || elapsed=$CHECK_INTERVAL
if [ "$elapsed" -lt "$CHECK_INTERVAL" ]; then
  exit 0
fi

remote_ver=$(curl -sf --max-time 5 "$DIST_TAGS_URL" \
  | sed -n 's/.*"latest"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
  | head -1 || true)

if [ -z "$remote_ver" ]; then
  exit 0
fi

tmp_config=$(mktemp 2>/dev/null || echo "${CONFIG_FILE}.tmp.$$")
if [ -f "$CONFIG_FILE" ]; then
  grep -v "^last_check=" "$CONFIG_FILE" > "$tmp_config" 2>/dev/null || true
fi
echo "last_check=$now" >> "$tmp_config"
mv "$tmp_config" "$CONFIG_FILE"

local_tag=$(read_local_version)
local_ver=${local_tag#v}
if [ -z "$local_ver" ] || [ "$local_ver" = "$remote_ver" ]; then
  exit 0
fi

cat <<EOF
GetAgent skill update available.
  Installed: v$local_ver
  Latest:    v$remote_ver
Update with:
  npx ${NPM_PACKAGE}@latest install --client <claude|cursor|codex|all>
EOF
