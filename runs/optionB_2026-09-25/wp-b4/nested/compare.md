# Study Comparison: jh63_go_gate_nested_purge_001856a6

**Description:** Nested Go-gate on freeze 001856a6 (Option B 9-feature) with locked-test trading-day purge aligned to expanding4; matrix C winner hparams; Go UNCLAIMED

- **Launch Git SHA:** `71d6f5fe112627f35cc99950672f8577b3908920`
- **Dataset Hash:** `001856a6b70801edefb578c37687be1555269de852baf7794294f2a51bce2034`
- **Total Runs:** 3 (Completed: 3, Aborted: 0)
- **Promotion Decision:** `rejected`

| Run ID | Config | Seed | Method | Calib | Threshold | Test F1 | Test P | Test R | Test Fβ | AUPRC | Brier | Confusion (TP/FP/TN/FN) | N+ Test | Wall (s) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `run_001_c035b7c8_s7` | `c035b7c8` | 7 | train_val_fbeta_0.5 | isotonic | 0.150 | 0.1793 | 0.1263 | 0.3090 | 0.1793 | 0.1349 | 0.1339 | 72/498/1051/161 | 233 | 1.11 | OK |
| `run_002_2ba2f1aa_s123` | `2ba2f1aa` | 123 | train_val_fbeta_0.5 | isotonic | 0.200 | 0.1467 | 0.1006 | 0.2704 | 0.1467 | 0.1525 | 0.1451 | 63/563/986/170 | 233 | 1.16 | OK |
| `run_000_2a42d7dc_s42` | `2a42d7dc` | 42 | train_val_fbeta_0.5 | isotonic | 0.150 | 0.0951 | 0.0806 | 0.1159 | 0.0951 | 0.1321 | 0.1398 | 27/308/1241/206 | 233 | 1.49 | OK |

## Promotion Gate (JH-AG-93.1)

- **Gate Decision:** `rejected` (Harness proposal only; Model Quality Go requires human review)
- **Target Floors:** F1 ≥ 0.30, Precision ≥ 0.25, AUPRC ≥ 0.18 (All must clear)
- **Required Extra Seeds:** `[7, 123]`
- **Seeds Cleared:** `[]`
- **Seeds Failed:** `[42, 7, 123]`

### Shortlisted Candidates & Multi-Seed Rollup

| Rank | Primary Run | Config | Seed | Test F1 | Test P | AUPRC | Confusion (TP/FP/TN/FN) | N+ Test | Floor Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `run_000_2a42d7dc_s42` | `2a42d7dc` | 42 | 0.0951 | 0.0806 | 0.1321 | 27/308/1241/206 | 233 | FAIL (f1 (0.0951 < 0.3000), precision (0.0806 < 0.2500), auprc (0.1321 < 0.1800)) |
| 1 | `run_001_c035b7c8_s7` | `2a42d7dc` | 7 | 0.1793 | 0.1263 | 0.1349 | 72/498/1051/161 | 233 | FAIL (f1 (0.1793 < 0.3000), precision (0.1263 < 0.2500), auprc (0.1349 < 0.1800)) |
| 1 | `run_002_2ba2f1aa_s123` | `2a42d7dc` | 123 | 0.1467 | 0.1006 | 0.1525 | 63/563/986/170 | 233 | FAIL (f1 (0.1467 < 0.3000), precision (0.1006 < 0.2500), auprc (0.1525 < 0.1800)) |

**Gate Notes:** Promotion gate rejected: no shortlisted candidate cleared all required extra seeds [7, 123] across floors (F1>=0.3, P>=0.25, AUPRC>=0.18).

> **Notice:** Harness proposal (`candidate` / `rejected` / `none`) is an automated
> multi-seed stability check. It does NOT constitute a `Model Quality Go` or an
> economic trading claim.
