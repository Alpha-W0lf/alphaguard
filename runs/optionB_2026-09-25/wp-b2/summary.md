# WP-B2 Rebuild freeze

**Status:** PASS · 2026-09-25 CT  
**Old freeze:** `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`  
**New freeze:** `001856a6b70801edefb578c37687be1555269de852baf7794294f2a51bce2034` (`<NEW8>=001856a6`)  
**n:** 8907 (Verified)  
**Label prevalence:** 0.16908049848433815 / n_pos=1506 (identical to backup; Verified)  
**FinBERT:** exact-identical on all 8907 event_id joins (Verified)  
**NaN count (9 features):** 0 (Verified)  
**Script:** `scripts/build_training_events.py --target-rows 8907 --skip-download --allow-shortfall` (FinBERT on)  
**Artifacts:** `check.json`, `build.log`

Note: legacy 5 price columns are not byte-identical to the 534a backup after a fresh yfinance pull (Yahoo adjust drift). Labels and FinBERT are identical. Hash change is expected from both new features and price refresh.

**Model Quality Go: UNCLAIMED**
