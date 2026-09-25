#!/usr/bin/env python3
"""Apply minimum G3 served_universe primary-verdict glue in-place on option-b worktree.

Changes:
1. SplitData gains optional test_served_mask
2. split_for_walk_forward populates mask when served_universe column present
3. execute_run: when mask present, metrics['test'] = served locked-test (primary);
   metrics['test_all'] = full locked-test (secondary report-only)
4. Does NOT add eval_slices to StudyMatrixConfig (schema blocker — documented in E3 summary)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# --- train_option_b.py: extend SplitData ---
tob = ROOT / "src/alphaguard/ml/train_option_b.py"
text = tob.read_text()
old = '''@dataclass(frozen=True)
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    train_start: str
    train_end: str
'''
new = '''@dataclass(frozen=True)
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    train_start: str
    train_end: str
    # Optional G3 mask: True for locked-test rows with served_universe==True.
    # When set, study_executor scores primary metrics['test'] on this slice.
    test_served_mask: np.ndarray | None = None
'''
if "test_served_mask" not in text:
    if old not in text:
        raise SystemExit("SplitData block not found in train_option_b.py")
    tob.write_text(text.replace(old, new, 1))
    print("patched train_option_b.py SplitData")
else:
    print("train_option_b.py already has test_served_mask")

# --- study_walkforward.py: populate mask ---
wf = ROOT / "src/alphaguard/ml/study_walkforward.py"
wtext = wf.read_text()
if "test_served_mask" not in wtext:
    # Add helper after imports / near top of split helpers
    helper = '''
def _test_served_mask(test_df: pd.DataFrame) -> np.ndarray | None:
    """Boolean mask over locked-test rows when served_universe column exists."""
    if "served_universe" not in test_df.columns:
        return None
    return test_df["served_universe"].astype(bool).to_numpy()

'''
    # Insert before resolve_locked_test_boundary
    anchor = "def resolve_locked_test_boundary("
    if anchor not in wtext:
        raise SystemExit("resolve_locked_test_boundary not found")
    wtext = wtext.replace(anchor, helper + anchor, 1)

    # Patch both SplitData constructions in split_for_walk_forward that build test=
    # Pattern: return SplitData( ... y_test=... train_start=... train_end=... )
    # We'll do a more careful replace of the two blocks that set test = df.iloc[boundary:]

    # Block 1: date-anchor no-session path
    b1_old = '''            train = df.iloc[:boundary]
            test = df.iloc[boundary:]
            return SplitData(
                x_train=train[names].to_numpy(dtype=float),
                y_train=train["label_high_risk"].to_numpy(dtype=int),
                x_test=test[names].to_numpy(dtype=float),
                y_test=test["label_high_risk"].to_numpy(dtype=int),
                train_start=str(train["published_at"].iloc[0]),
                train_end=str(train["published_at"].iloc[-1]),
            )'''
    b1_new = '''            train = df.iloc[:boundary]
            test = df.iloc[boundary:]
            return SplitData(
                x_train=train[names].to_numpy(dtype=float),
                y_train=train["label_high_risk"].to_numpy(dtype=int),
                x_test=test[names].to_numpy(dtype=float),
                y_test=test["label_high_risk"].to_numpy(dtype=int),
                train_start=str(train["published_at"].iloc[0]),
                train_end=str(train["published_at"].iloc[-1]),
                test_served_mask=_test_served_mask(test),
            )'''
    if b1_old not in wtext:
        raise SystemExit("date-anchor SplitData block not found")
    wtext = wtext.replace(b1_old, b1_new, 1)

    b2_old = '''    train = df.iloc[:train_end]
    test = df.iloc[boundary:]
    return SplitData(
        x_train=train[names].to_numpy(dtype=float),
        y_train=train["label_high_risk"].to_numpy(dtype=int),
        x_test=test[names].to_numpy(dtype=float),
        y_test=test["label_high_risk"].to_numpy(dtype=int),
        train_start=str(train["published_at"].iloc[0]),
        train_end=str(train["published_at"].iloc[-1]),
    )'''
    b2_new = '''    train = df.iloc[:train_end]
    test = df.iloc[boundary:]
    return SplitData(
        x_train=train[names].to_numpy(dtype=float),
        y_train=train["label_high_risk"].to_numpy(dtype=int),
        x_test=test[names].to_numpy(dtype=float),
        y_test=test["label_high_risk"].to_numpy(dtype=int),
        train_start=str(train["published_at"].iloc[0]),
        train_end=str(train["published_at"].iloc[-1]),
        test_served_mask=_test_served_mask(test),
    )'''
    if b2_old not in wtext:
        raise SystemExit("purged SplitData block not found")
    wtext = wtext.replace(b2_old, b2_new, 1)
    wf.write_text(wtext)
    print("patched study_walkforward.py")
else:
    print("study_walkforward.py already has test_served_mask")

# --- study_executor.py: primary = served when mask present ---
ex = ROOT / "src/alphaguard/ml/study_executor.py"
etext = ex.read_text()
marker = "metrics_map[\"test_all\"]"
if marker in etext:
    print("study_executor.py already has test_all served glue")
else:
    old_block = '''    test_metrics_dict = compute_metrics_suite(
        split.y_test, test_probs, threshold=threshold, beta=config.beta
    )
    test_confusion = ConfusionMatrix(**test_metrics_dict["confusion"])
    metrics_map["test"] = SplitMetrics(
        n_samples=test_metrics_dict["n_samples"],
        n_positive=test_metrics_dict["n_positive"],
        prevalence=test_metrics_dict["prevalence"],
        threshold=threshold,
        beta=config.beta,
        precision=test_metrics_dict["precision"],
        recall=test_metrics_dict["recall"],
        f1=test_metrics_dict["f1"],
        fbeta=test_metrics_dict["fbeta"],
        auprc=test_metrics_dict["auprc"],
        brier=test_metrics_dict["brier"],
        confusion=test_confusion,
    )'''
    new_block = '''    test_all_metrics_dict = compute_metrics_suite(
        split.y_test, test_probs, threshold=threshold, beta=config.beta
    )
    # G3: when served_universe mask is present, primary metrics["test"] is the
    # served locked-test slice; full-universe locked-test is metrics["test_all"].
    served_mask = getattr(split, "test_served_mask", None)
    if served_mask is not None and int(np.asarray(served_mask).sum()) > 0:
        mask = np.asarray(served_mask, dtype=bool)
        metrics_map["test_all"] = SplitMetrics(
            n_samples=test_all_metrics_dict["n_samples"],
            n_positive=test_all_metrics_dict["n_positive"],
            prevalence=test_all_metrics_dict["prevalence"],
            threshold=threshold,
            beta=config.beta,
            precision=test_all_metrics_dict["precision"],
            recall=test_all_metrics_dict["recall"],
            f1=test_all_metrics_dict["f1"],
            fbeta=test_all_metrics_dict["fbeta"],
            auprc=test_all_metrics_dict["auprc"],
            brier=test_all_metrics_dict["brier"],
            confusion=ConfusionMatrix(**test_all_metrics_dict["confusion"]),
        )
        test_metrics_dict = compute_metrics_suite(
            split.y_test[mask], test_probs[mask], threshold=threshold, beta=config.beta
        )
        logger.info(
            "G3 primary locked-test = served_universe slice n=%s pos=%s (full n=%s)",
            test_metrics_dict["n_samples"],
            test_metrics_dict["n_positive"],
            test_all_metrics_dict["n_samples"],
        )
    else:
        test_metrics_dict = test_all_metrics_dict
    test_confusion = ConfusionMatrix(**test_metrics_dict["confusion"])
    metrics_map["test"] = SplitMetrics(
        n_samples=test_metrics_dict["n_samples"],
        n_positive=test_metrics_dict["n_positive"],
        prevalence=test_metrics_dict["prevalence"],
        threshold=threshold,
        beta=config.beta,
        precision=test_metrics_dict["precision"],
        recall=test_metrics_dict["recall"],
        f1=test_metrics_dict["f1"],
        fbeta=test_metrics_dict["fbeta"],
        auprc=test_metrics_dict["auprc"],
        brier=test_metrics_dict["brier"],
        confusion=test_confusion,
    )'''
    if old_block not in etext:
        raise SystemExit("executor test metrics block not found")
    etext = etext.replace(old_block, new_block, 1)
    # Also fix n_positive_test to use primary (served) count — already uses test_metrics via
    # split.y_test.sum() at the end; update to primary when mask present.
    old_npos = "n_positive_test=int(split.y_test.sum()),"
    new_npos = "n_positive_test=int(test_metrics_dict[\"n_positive\"]),"
    if old_npos not in etext:
        raise SystemExit("n_positive_test line not found")
    etext = etext.replace(old_npos, new_npos, 1)
    ex.write_text(etext)
    print("patched study_executor.py")

print("DONE")
