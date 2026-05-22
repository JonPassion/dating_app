#!/usr/bin/env bash
# Deploy JonPassion/dating_app blueprint via Render API
set -euo pipefail

REPO_URL="${RENDER_REPO_URL:-https://github.com/JonPassion/dating_app}"
BRANCH="${RENDER_BRANCH:-main}"

if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "Error: Set RENDER_API_KEY (from https://dashboard.render.com/u/settings#api-keys)"
  echo ""
  echo "  export RENDER_API_KEY=rnd_xxxxxxxx"
  echo "  ./scripts/deploy-render.sh"
  echo ""
  echo "Or use one-click deploy:"
  echo "  https://render.com/deploy?repo=${REPO_URL}"
  exit 1
fi

echo "Fetching Render owner ID..."
OWNER_ID=$(curl -sf "https://api.render.com/v1/owners?limit=20" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['owner']['id'] if d else '')")

if [ -z "$OWNER_ID" ]; then
  echo "Error: Could not list Render owners. Check RENDER_API_KEY."
  exit 1
fi

echo "Deploying blueprint from ${REPO_URL} (branch: ${BRANCH})..."
RESPONSE=$(curl -sf -X POST "https://api.render.com/v1/blueprints" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"repo\":\"${REPO_URL}\",\"branch\":\"${BRANCH}\",\"ownerId\":\"${OWNER_ID}\"}")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""
echo "Done. Open https://dashboard.render.com/ to watch the deploy."
