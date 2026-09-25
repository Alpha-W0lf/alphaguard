# Study Comparison: jh63_wf_expanding4_001856a6

**Description:** expanding4 walk-forward purge-on on freeze 001856a6 (Option B 9-feature); matrix C winner hparams; Go UNCLAIMED; compare to Phase B 534a purge-on

- **Launch Git SHA:** `71d6f5fe112627f35cc99950672f8577b3908920`
- **Dataset Hash:** `001856a6b70801edefb578c37687be1555269de852baf7794294f2a51bce2034`
- **Total Runs:** 5 (Completed: 5, Aborted: 0)
- **Promotion Decision:** `none`

| Run ID | Config | Seed | Method | Calib | Threshold | Test F1 | Test P | Test R | Test Fβ | AUPRC | Brier | Confusion (TP/FP/TN/FN) | N+ Test | Wall (s) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `run_002_869ec9e1_s2` | `869ec9e1` | 2 | train_f1_max | isotonic | 0.300 | 0.1979 | 0.1421 | 0.3262 | 0.1979 | 0.1444 | 0.1373 | 76/459/1090/157 | 233 | 2.30 | OK |
| `run_000_e76d107d_s0` | `e76d107d` | 0 | train_f1_max | isotonic | 0.150 | 0.1773 | 0.1185 | 0.3519 | 0.1773 | 0.1362 | 0.1449 | 82/610/939/151 | 233 | 2.56 | OK |
| `run_004_0e8a509c_s4` | `0e8a509c` | 4 | train_f1_max | isotonic | 0.250 | 0.1667 | 0.1232 | 0.2575 | 0.1667 | 0.1290 | 0.1443 | 60/427/1122/173 | 233 | 2.19 | OK |
| `run_001_d62c0c0b_s1` | `d62c0c0b` | 1 | train_f1_max | isotonic | 0.300 | 0.1404 | 0.1054 | 0.2103 | 0.1404 | 0.1310 | 0.1580 | 49/416/1133/184 | 233 | 2.19 | OK |
| `run_003_f0e88fce_s3` | `f0e88fce` | 3 | train_f1_max | isotonic | 0.400 | 0.1385 | 0.0937 | 0.2661 | 0.1385 | 0.1287 | 0.1788 | 62/600/949/171 | 233 | 2.31 | OK |

## Promotion Gate (JH-AG-93.1)

- **Promotion Decision:** `none`
- **Status:** No promotion gate configured for this study.

> **Notice:** Harness proposal (`candidate` / `rejected` / `none`) is an automated
> multi-seed stability check. It does NOT constitute a `Model Quality Go` or an
> economic trading claim.
