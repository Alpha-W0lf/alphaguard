# WP-B1 Feature code and tests

**Status:** COMPLETE · 2026-09-25 CT  
**Freeze:** still `534a341a…` until WP-B2 rebuild  
**Model Quality Go: UNCLAIMED**

## Changes
- `dataset_asof.py`: `_vol_window`, `_drawdown_window`; `_vol_20d` thin wrapper; `rs_20d`, `drawdown_20d`, `volatility_5d`, `spy_volatility_20d` in `compute_features_and_label`
- `decisions.py`: FEATURE_NAMES appends the four names after the original five
- `dataset_build.py`: REQUIRED_COLUMNS includes the four
- Fixtures + `build_fixture_bundle.py` logits updated; gate refuse-on-skew unchanged
- `docs/TRAINING_DATA.md` feature table
- Tests: `tests/test_option_b_features.py`; legacy 534a backup audit kept

## Pytest
Verified: `187 passed, 1 skipped, 6 deselected` — see `pytest_full.txt`
