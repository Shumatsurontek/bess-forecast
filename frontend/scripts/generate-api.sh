#!/usr/bin/env bash
set -euo pipefail
BASE="${VITE_API_BASE_URL:-http://localhost:8000}"
echo "Fetching OpenAPI spec from $BASE/openapi.json"
curl -fsSL "$BASE/openapi.json" -o openapi.json
npx openapi-typescript-codegen \
  --input openapi.json \
  --output src/api \
  --client fetch \
  --useOptions \
  --useUnionTypes \
  --indent 2
echo "Generated client at src/api/"
