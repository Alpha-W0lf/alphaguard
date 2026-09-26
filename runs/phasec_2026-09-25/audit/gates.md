# Phase C gates

Model Quality Go remains UNCLAIMED. This audit does not propose a candidate.

- Freeze: `534a341a9d89f1266b11a7d4fff305575dcf4c2cc6c766e3d786047ddf042cb3`
- Gate (a) fired: True
- Gate (b) fired: True
- Gate (c) fired: True (misaligned)
- WP-C5 fired: True
- Overlap rows after trading-day purge: 0

## Gate (a) reasons

- C3 horizon overlaps on the 5-row embargo=229
- C3 5-row embargo is shorter than 5 feature sessions on 5 boundaries

## Fold verdicts

- fold_0: **artifact** prevalence=0.16666666666666666 reasons=one_ticker
- fold_1: **regime** prevalence=0.2806361085126286 reasons=spread_and_market_drawdown
- fold_2: **regime** prevalence=0.17586529466791395 reasons=spread_and_market_drawdown
- fold_3: **regime** prevalence=0.17305893358278765 reasons=spread_and_market_drawdown
- locked_test: **regime** prevalence=0.1307519640852974 reasons=spread_and_market_drawdown

## Rules alignment

Verdict: **misaligned** (2/4 folds, veto rate higher).

| slice | veto positive rate | non-veto positive rate | veto higher |
| --- | --- | --- | --- |
| fold_0 | 0.15934065934065933 | 0.16817155756207675 | False |
| fold_1 | 0.24548736462093862 | 0.29292929292929293 | False |
| fold_2 | 0.2564102564102564 | 0.15789473684210525 | True |
| fold_3 | 0.2261904761904762 | 0.16852791878172588 | True |
| locked_test | 0.3680555555555556 | 0.08500669344042838 | True |
