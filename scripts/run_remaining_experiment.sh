#!/bin/bash
# Session 09 -- Remaining conditions after credit recharge
# Already completed: full/A, no_repair/A, no_verify/A
# Remaining: no_taint/A, baseline_pure_llm/A, baseline_langchain/A,
#            full/B, no_repair/B, baseline_pure_llm/B

cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
PYTHON=python3.11

DATASET_A="datasets/dataset_a"
DATASET_B="datasets/dataset_b"
RESULTS="results/session_09"
SAMPLE=$(cat scripts/dataset_a_sample.txt | tr '\n' ' ')

check_spend() {
  $PYTHON -c "
import json, glob
files = [f for f in glob.glob('results/session_09/**/*.json', recursive=True)
         if not f.split('/')[-1].startswith('summary_')]
if not files:
    print('No results yet.')
else:
    total_in = sum(json.load(open(f)).get('total_input_tokens',0) for f in files)
    total_out = sum(json.load(open(f)).get('total_output_tokens',0) for f in files)
    cost = total_in/1e6*5 + total_out/1e6*25
    print(f'Cumulative spend: \${cost:.4f} USD ({len(files)} tasks completed)')
"
}

echo "=== Session 09 -- Remaining Conditions ==="
echo ""

echo "--- Dataset A: condition=no_taint ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_taint \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --budget 80 \
  --tasks $SAMPLE

echo "--- Dataset A: baseline_pure_llm ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_A \
  --results $RESULTS \
  --budget 80 \
  --tasks $SAMPLE

echo "--- Dataset A: baseline_langchain ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_langchain \
  --dataset $DATASET_A \
  --results $RESULTS \
  --budget 80 \
  --tasks $SAMPLE

echo "--- Dataset B: condition=full ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition full \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch \
  --budget 80

echo "--- Dataset B: condition=no_repair ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_repair \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch \
  --budget 80

echo "--- Dataset B: baseline_pure_llm ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_B \
  --results $RESULTS \
  --budget 80

echo ""
echo "=== Remaining conditions complete ==="
check_spend
