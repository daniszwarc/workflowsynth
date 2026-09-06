#!/bin/bash
# Session 09 -- Full experiment run
# Dataset A sample (60 tasks) + Dataset B (60 tasks), all conditions
# Estimated cost: ~$55 USD

cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
PYTHON=python3.11

DATASET_A="datasets/dataset_a"
DATASET_B="datasets/dataset_b"
RESULTS="results/session_09"
SAMPLE=$(cat scripts/dataset_a_sample.txt | tr '\n' ' ')
BUDGET=55

check_spend() {
  $PYTHON -c "
import json, glob
files = glob.glob('results/session_09/**/*.json', recursive=True)
if not files:
    print('No results yet.')
else:
    total_in = sum(json.load(open(f)).get('total_input_tokens',0) for f in files)
    total_out = sum(json.load(open(f)).get('total_output_tokens',0) for f in files)
    cost = total_in/1e6*5 + total_out/1e6*25
    print(f'Cumulative spend: \${cost:.4f} USD ({len(files)} tasks completed)')
"
}

echo "=== Session 09 Full Experiment Run ==="
echo "Dataset A sample: 60 tasks"
echo "Dataset B: 60 tasks"
echo "Conditions: full, no_repair, no_verify, no_taint, baseline_pure_llm, baseline_langchain"
echo ""

# Dataset A -- condition=full (Batch API)
echo "--- Dataset A: condition=full ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition full \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset A -- condition=no_repair (single attempt, no batch needed)
echo "--- Dataset A: condition=no_repair ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_repair \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset A -- condition=no_verify
echo "--- Dataset A: condition=no_verify ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_verify \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset A -- condition=no_taint
echo "--- Dataset A: condition=no_taint ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_taint \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset A -- PureLLM baseline
echo "--- Dataset A: baseline_pure_llm ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_A \
  --results $RESULTS \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset A -- LangChain baseline
echo "--- Dataset A: baseline_langchain ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_langchain \
  --dataset $DATASET_A \
  --results $RESULTS \
  --budget $BUDGET \
  --tasks $SAMPLE

# Dataset B -- condition=full (Batch API)
echo "--- Dataset B: condition=full ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition full \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch \
  --budget $BUDGET

# Dataset B -- condition=no_repair
echo "--- Dataset B: condition=no_repair ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition no_repair \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch \
  --budget $BUDGET

# Dataset B -- PureLLM baseline
echo "--- Dataset B: baseline_pure_llm ---"
check_spend
$PYTHON scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_B \
  --results $RESULTS \
  --budget $BUDGET

echo ""
echo "=== Experiment complete ==="
echo "Results at: $RESULTS"
