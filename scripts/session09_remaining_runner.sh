#!/bin/bash
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
export PYTHONPATH="$PWD"
PYTHON=python3.11

LOG=/private/tmp/claude-501/-Users-daniszwarc-Desktop-ClaudeCode-workflowsynth/ffb1c89b-4460-40df-afd5-977b426799eb/scratchpad/session09_remaining_run.log
: > "$LOG"

run_step() {
  local desc="$1"; shift
  echo "=== $desc ===" | tee -a "$LOG"
  yes y | "$@" >>"$LOG" 2>&1
  echo "--- exit code: $? ---" | tee -a "$LOG"
}

run_step "no_verify / Dataset B" $PYTHON scripts/run_evaluation.py \
  --condition no_verify --dataset datasets/dataset_b --results results/session_09 \
  --batch --budget 40

run_step "no_taint / Dataset B" $PYTHON scripts/run_evaluation.py \
  --condition no_taint --dataset datasets/dataset_b --results results/session_09 \
  --batch --budget 40

run_step "baseline_langchain / Dataset B" $PYTHON scripts/run_evaluation.py \
  --condition baseline_langchain --dataset datasets/dataset_b --results results/session_09 \
  --budget 40

run_step "baseline_langchain / Dataset A (23 contaminated tasks)" $PYTHON scripts/run_evaluation.py \
  --condition baseline_langchain --dataset datasets/dataset_a --results results/session_09 \
  --budget 40 \
  --tasks wf_mm_008 wf_ms_009 wf_mvp_001 wf_mvp_002 wf_mvp_003 \
          wf_mvp_010 wf_pb_001 wf_pb_002 wf_pb_004 wf_pb_005 \
          wf_pb_006 wf_pb_007 wf_pb_008 wf_pb_009 wf_pb_010 \
          wf_sv_001 wf_sv_002 wf_sv_003 wf_sv_004 wf_sv_005 \
          wf_sv_006 wf_ts_001 wf_ts_002

echo "=== analyze_results ===" | tee -a "$LOG"
$PYTHON scripts/analyze_results.py > results/session_09/analysis_output.txt 2>&1
echo "--- exit code: $? ---" | tee -a "$LOG"

echo "=== git commit ===" | tee -a "$LOG"
git add results/session_09/ >>"$LOG" 2>&1
git commit -m "$(cat <<'EOF'
feat(results): Session 09 complete -- all conditions both datasets

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)" >>"$LOG" 2>&1
echo "--- exit code: $? ---" | tee -a "$LOG"

echo "ALL DONE" | tee -a "$LOG"
