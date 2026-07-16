#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${ROOT_DIR}/artifacts/qwen3-vl-8b/qlora"
LOG_FILE="${RUN_ROOT}/train_v1.log"
GPU_LOG="${RUN_ROOT}/train_v1_gpu_memory.csv"
STATUS_FILE="${RUN_ROOT}/train_v1_status.txt"

cd "${ROOT_DIR}"
mkdir -p "${RUN_ROOT}"

{
  echo "STARTED_AT=$(date --iso-8601=seconds)"
  echo "CONFIG=configs/qwen3_vl_8b_qlora_train.yaml"
} > "${STATUS_FILE}"

nvidia-smi \
  --query-gpu=timestamp,memory.used,utilization.gpu \
  --format=csv,noheader,nounits \
  -l 1 > "${GPU_LOG}" &
MONITOR_PID=$!

cleanup() {
  kill "${MONITOR_PID}" 2>/dev/null || true
  wait "${MONITOR_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

PYTORCH_ALLOC_CONF=expandable_segments:True \
  llamafactory-cli train configs/qwen3_vl_8b_qlora_train.yaml \
  2>&1 | tee "${LOG_FILE}"
TRAIN_STATUS=${PIPESTATUS[0]}

cleanup
trap - EXIT INT TERM

PEAK_MIB=$(awk -F, '{gsub(/ /, "", $2); if (($2 + 0) > max) max=$2 + 0} END {print max + 0}' "${GPU_LOG}")
{
  echo "FINISHED_AT=$(date --iso-8601=seconds)"
  echo "TRAIN_EXIT=${TRAIN_STATUS}"
  echo "NVIDIA_SMI_PEAK_MIB=${PEAK_MIB}"
} >> "${STATUS_FILE}"

exit "${TRAIN_STATUS}"
