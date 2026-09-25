#!/bin/bash
set -euo pipefail
cd /Users/tom/Documents/Git/alphaguard-wt-option-b
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 XGB_NUM_THREAD=1
PY=.venv/bin/python
W=runs/sample_expand_2026-09-25/wp-e1/perm_batch_worker.py
LOG=runs/sample_expand_2026-09-25/wp-e1/e1_batch_stdout.log
CKPT=runs/sample_expand_2026-09-25/wp-e1/permutation_checkpoint.json
BS=10

START=$($PY -c "import json,pathlib; p=pathlib.Path('$CKPT'); print(len(json.loads(p.read_text())['null_scores']) if p.exists() else 0)")
echo "$(date -Iseconds) Starting batches from $START step=$BS" | tee -a "$LOG"

s=$START
while [ "$s" -lt 200 ]; do
  e=$((s+BS))
  if [ "$e" -gt 200 ]; then e=200; fi
  echo "=== batch [$s,$e) ===" | tee -a "$LOG"
  if ! $PY -u "$W" "$s" "$e" >> "$LOG" 2>&1; then
    echo "BATCH FAIL at [$s,$e) exit=$?" | tee -a "$LOG"
    exit 1
  fi
  sleep 1
  s=$e
done
echo "ALL BATCHES DONE" | tee -a "$LOG"
