#!/bin/bash
# Session 09 -- Full experiment run
# Dataset A sample (60 tasks) + Dataset B (60 tasks), all conditions
# Estimated cost: ~$55 USD

DATASET_A="datasets/dataset_a"
DATASET_B="datasets/dataset_b"
RESULTS="results/session_09"
SAMPLE=$(cat scripts/dataset_a_sample.txt | tr '\n' ' ')

echo "=== Session 09 Full Experiment Run ==="
echo "Dataset A sample: 60 tasks"
echo "Dataset B: 60 tasks"
echo "Conditions: full, no_repair, no_verify, no_taint, baseline_pure_llm, baseline_langchain"
echo ""

# Dataset A -- condition=full (Batch API)
echo "--- Dataset A: condition=full ---"
python scripts/run_evaluation.py \
  --condition full \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --tasks $SAMPLE

# Dataset A -- condition=no_repair (single attempt, no batch needed)
echo "--- Dataset A: condition=no_repair ---"
python scripts/run_evaluation.py \
  --condition no_repair \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --tasks $SAMPLE

# Dataset A -- condition=no_verify
echo "--- Dataset A: condition=no_verify ---"
python scripts/run_evaluation.py \
  --condition no_verify \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --tasks $SAMPLE

# Dataset A -- condition=no_taint
echo "--- Dataset A: condition=no_taint ---"
python scripts/run_evaluation.py \
  --condition no_taint \
  --dataset $DATASET_A \
  --results $RESULTS \
  --batch \
  --tasks $SAMPLE

# Dataset A -- PureLLM baseline
echo "--- Dataset A: baseline_pure_llm ---"
python scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_A \
  --results $RESULTS \
  --tasks $SAMPLE

# Dataset A -- LangChain baseline
echo "--- Dataset A: baseline_langchain ---"
python scripts/run_evaluation.py \
  --condition baseline_langchain \
  --dataset $DATASET_A \
  --results $RESULTS \
  --tasks $SAMPLE

# Dataset B -- condition=full (Batch API)
echo "--- Dataset B: condition=full ---"
python scripts/run_evaluation.py \
  --condition full \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch

# Dataset B -- condition=no_repair
echo "--- Dataset B: condition=no_repair ---"
python scripts/run_evaluation.py \
  --condition no_repair \
  --dataset $DATASET_B \
  --results $RESULTS \
  --batch

# Dataset B -- PureLLM baseline
echo "--- Dataset B: baseline_pure_llm ---"
python scripts/run_evaluation.py \
  --condition baseline_pure_llm \
  --dataset $DATASET_B \
  --results $RESULTS

echo ""
echo "=== Experiment complete ==="
echo "Results at: $RESULTS"
