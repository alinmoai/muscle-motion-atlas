#!/usr/bin/env bash
# Download the two Z-Anatomy source models (pinned commit) into build/source and check their hashes.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)/build/source"
mkdir -p "$DIR"
COMMIT=6c7f9016bd5899ac8edafd31b9900c151df42ed6   # LluisV/Z-Anatomy, branch PC-Version
BASE="https://raw.githubusercontent.com/LluisV/Z-Anatomy/$COMMIT/Resources/Models/FBX"
declare -A SHA=(
  [SkeletalSystem100.fbx]=294a649765cd060a62a4095da52b9c8ef2d97769aa447e196448aa5f7d596dea
  [MuscularSystem100.fbx]=4c19df534d5d84aabbce08604306aa0485b43e8a2483c72a95b569e1dfea2279
)
for f in "${!SHA[@]}"; do
  if [ -f "$DIR/$f" ] && echo "${SHA[$f]}  $DIR/$f" | sha256sum -c --status; then
    echo "ok (cached) $f"; continue
  fi
  echo "downloading $f"
  curl -fsSL --retry 3 -o "$DIR/$f" "$BASE/$f"
  echo "${SHA[$f]}  $DIR/$f" | sha256sum -c
done
