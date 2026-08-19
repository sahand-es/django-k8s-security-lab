#!/usr/bin/env bash
set -euo pipefail

CTF_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CTF_ROOT"

for img in backend admin-panel escape-zone; do
  echo ">>> building ctf/$img"
  docker build -t "ctf/$img:latest" "./services/$img"
  echo ">>> loading ctf/$img into kind"
  kind load docker-image "ctf/$img:latest" --name ctf
done

echo "Done. Images: $(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^ctf/' | tr '\n' ' ')"
