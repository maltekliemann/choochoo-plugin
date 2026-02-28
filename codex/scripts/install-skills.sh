#!/usr/bin/env bash
set -euo pipefail

OVERWRITE=0
if [[ "${1:-}" == "--overwrite" ]]; then
  OVERWRITE=1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/../skills"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
DEST_DIR="${CODEX_HOME_DIR}/skills"

mkdir -p "${DEST_DIR}"

installed=0
skipped=0

for skill_path in "${SRC_DIR}"/*; do
  [[ -d "${skill_path}" ]] || continue
  skill_name="$(basename "${skill_path}")"
  target_path="${DEST_DIR}/${skill_name}"

  if [[ -e "${target_path}" && "${OVERWRITE}" -ne 1 ]]; then
    echo "skip   ${skill_name} (already exists, use --overwrite)"
    skipped=$((skipped + 1))
    continue
  fi

  if [[ -e "${target_path}" ]]; then
    rm -rf "${target_path}"
  fi

  cp -R "${skill_path}" "${target_path}"
  echo "install ${skill_name}"
  installed=$((installed + 1))
done

echo
echo "Installed: ${installed}"
echo "Skipped:   ${skipped}"
echo "Target:    ${DEST_DIR}"
