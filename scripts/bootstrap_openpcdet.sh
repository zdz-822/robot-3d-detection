#!/usr/bin/env bash
set -euo pipefail

target="${1:-$HOME/projects/robot-3d-detection/OpenPCDet}"
parent="$(dirname "$target")"

if [[ -f "$target/setup.py" && -d "$target/pcdet" ]]; then
  echo "OpenPCDet source is already available: $target"
  exit 0
fi

mkdir -p "$parent"
if [[ -e "$target" ]]; then
  echo "Target exists but is incomplete: $target" >&2
  echo "Move or remove that incomplete directory, then run this script again." >&2
  exit 1
fi

archive="${TMPDIR:-/tmp}/OpenPCDet-master.zip"
unpack_dir="$(mktemp -d)"
cleanup() { rm -rf "$unpack_dir"; }
trap cleanup EXIT

# The archive is from GitHub's official codeload endpoint. --continue-at lets a
# slow or interrupted connection resume without re-downloading completed bytes.
curl --fail --location --retry 20 --retry-all-errors --retry-delay 5 \
  --continue-at - https://codeload.github.com/open-mmlab/OpenPCDet/zip/refs/heads/master \
  --output "$archive"

# Python's standard library avoids requiring a separate unzip system package.
python3 -m zipfile -e "$archive" "$unpack_dir"
mv "$unpack_dir/OpenPCDet-master" "$target"
echo "OpenPCDet source downloaded to: $target"
