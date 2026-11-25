#!/usr/bin/env bash
# Copy the pipeline's secrets from .env into the GitHub repository's Actions secrets.
# Values go to gh through stdin, so they never appear in the terminal or shell history.
# Needs a gh login with admin rights on the repository (gh auth login).
set -euo pipefail
REPO="${1:-skyyeom/kfood-exports}"
cd "$(dirname "$0")/.."
[ -f .env ] || { echo ".env not found; copy .env.example to .env and fill it in." >&2; exit 1; }
for name in DATABASE_URL SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY KCS_API_KEY COMTRADE_API_KEY; do
  value="$(sed -n "s/^${name}=//p" .env | head -1)"
  if [ -z "$value" ]; then echo "skip   $name (empty in .env)"; continue; fi
  printf '%s' "$value" | gh secret set "$name" -R "$REPO"
  echo "set    $name"
done
