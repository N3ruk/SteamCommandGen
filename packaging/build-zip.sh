#!/usr/bin/env bash
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
version="3.2.7"
out="${1:-$repo/dist}"
mkdir -p "$out"
out="$(cd "$out" && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
package="$tmp/SteamCommandGen-${version}"
mkdir -p "$package"
cp -a "$repo/src/SteamCommandGen.py" "$repo/src/SteamCommandGen.png" \
    "$repo/src/SteamCommandGen" "$repo/src/install.sh" \
    "$repo/src/uninstall.sh" "$repo/LICENSE" "$package/"
(cd "$tmp" && zip -qr "$out/SteamCommandGen-${version}.zip" "SteamCommandGen-${version}")
