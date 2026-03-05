#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_process_single_image.sh --input <path> --output <path> [options]

Required:
  --input <path>         Input image path
  --output <path>        Output mask path

Options:
  --checkpoint <path>    Model checkpoint (default: runs/unet_stomata_ddp/best.pt next to this script)
  --tile <int>           Tile size (default: 512)
  --overlap <int>        Tile overlap (default: 64)
  --threshold <float>    Binary threshold (default: 0.5)
  --env-name <name>      Conda env name (default: seg-stomate-cpu)
  --conda-base <path>    Conda base path (auto-detected if omitted)
  -h, --help             Show this help

Example:
  ./run_process_single_image.sh \
    --input images/img_001.tif \
    --output out.png \
    --env-name seg-stomate-cpu
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/process_single_image.py"

INPUT=""
OUTPUT=""
CHECKPOINT="${SCRIPT_DIR}/runs/unet_stomata_ddp/best.pt"
TILE="512"
OVERLAP="64"
THRESHOLD="0.5"
ENV_NAME="seg-stomate-cpu"
CONDA_BASE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --checkpoint)
      CHECKPOINT="$2"
      shift 2
      ;;
    --tile)
      TILE="$2"
      shift 2
      ;;
    --overlap)
      OVERLAP="$2"
      shift 2
      ;;
    --threshold)
      THRESHOLD="$2"
      shift 2
      ;;
    --env-name)
      ENV_NAME="$2"
      shift 2
      ;;
    --conda-base)
      CONDA_BASE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${INPUT}" || -z "${OUTPUT}" ]]; then
  echo "Error: --input and --output are required." >&2
  usage
  exit 1
fi

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "Error: Python script not found: ${PY_SCRIPT}" >&2
  exit 1
fi

if [[ -z "${CONDA_BASE}" ]]; then
  if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
  fi
fi

if [[ -z "${CONDA_BASE}" ]]; then
  for candidate in "$HOME/miniforge3" "$HOME/anaconda3" "$HOME/miniconda3"; do
    if [[ -f "${candidate}/etc/profile.d/conda.sh" ]]; then
      CONDA_BASE="${candidate}"
      break
    fi
  done
fi

if [[ -z "${CONDA_BASE}" || ! -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
  echo "Error: Could not find conda base. Pass --conda-base /path/to/conda" >&2
  exit 1
fi

source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

echo "Using conda env: ${ENV_NAME}"
echo "Running: ${PY_SCRIPT}"

python "${PY_SCRIPT}" \
  --input "${INPUT}" \
  --output "${OUTPUT}" \
  --checkpoint "${CHECKPOINT}" \
  --tile "${TILE}" \
  --overlap "${OVERLAP}" \
  --threshold "${THRESHOLD}"
