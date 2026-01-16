#!/usr/bin/env bash
set -euo pipefail

if [ -d web ]; then cd web
elif [ -d frontend ]; then cd frontend
elif [ -d ui ]; then cd ui
else
  echo "No frontend directory (web/frontend/ui) found."
  exit 0
fi

if [ -f pnpm-lock.yaml ]; then
  corepack enable >/dev/null 2>&1 || true
  pnpm install --frozen-lockfile
  PM="pnpm"
elif [ -f yarn.lock ]; then
  corepack enable >/dev/null 2>&1 || true
  yarn install --frozen-lockfile
  PM="yarn"
else
  if [ -f package-lock.json ]; then npm ci; else npm install; fi
  PM="npm"
fi

run() {
  local script="$1"
  if [ "$PM" = "pnpm" ]; then pnpm -s run "$script"
  elif [ "$PM" = "yarn" ]; then yarn -s "$script"
  else npm run -s "$script"
  fi
}

if node -e "p=require('./package.json');process.exit(p.scripts&&p.scripts.lint?0:1)" 2>/dev/null; then
  echo "== frontend: lint =="
  run lint
else
  echo "== frontend: lint (skipped; no script) =="
fi

if node -e "p=require('./package.json');process.exit(p.scripts&&p.scripts.test?0:1)" 2>/dev/null; then
  echo "== frontend: test =="
  run test
else
  echo "== frontend: test (skipped; no script) =="
fi

echo "== frontend: build =="
if [ -f next.config.js ] || [ -f next.config.mjs ] || [ -f next.config.ts ]; then
  if node -e "p=require('./package.json');process.exit(p.scripts&&p.scripts.build?0:1)" 2>/dev/null; then
    run build
  else
    npx -y next build
  fi
else
  if node -e "p=require('./package.json');process.exit(p.scripts&&p.scripts.build?0:1)" 2>/dev/null; then
    run build
  else
    npx -y vite build
  fi
fi
