# Tsunami Model Improvement Log

Track every iteration: what changed, what improved, what got worse.

## Baseline (Session 1 - 2026-03-27)

| Metric | Value | Notes |
|--------|-------|-------|
| Training set | 53 companies, 5 crash cycles | Hand-curated from SEC filings |
| Scoring method | Hand-tuned min/max + grid search | NOT the real algorithm from spec |
| Beta calculation | None -- fixed weights | Should use regression / Random Forest |
| Accuracy | 58% | (TP + TN) / Total |
| Precision | 71% | Of flagged, how many actually died |
| Recall | 53% | Of dead companies, how many flagged |
| True Positives | 17 | Correctly flagged + stayed dead |
| False Positives | 7 | Flagged but recovered (CRM, AMZN, PCLN, COIN, MSTR, DASH, GS) |
| True Negatives | 14 | Correctly skipped recoverers |
| False Negatives | 15 | Missed dead companies (ZM, CSCO, CHGG, etc.) |
| R-squared | Not calculated | Need to run real regression |
| ZM simulation | 310% ROI, 1 trade, 49 days | Entry 28 days after peak |

## Known Issues (to fix in next iteration)

| Issue | Impact | Fix |
|-------|--------|-----|
| ROIC overweighted in moat | False negatives (CSCO, ZM look healthy) | De-weight ROIC, add moat velocity |
| P/E gate is absolute | Misses low-P/E targets (Macy's, GE) | Dynamic gate = base / (1 + magnitude) |
| No moat velocity | Static moat misses eroding moats | effective_moat = current × velocity |
| Hand-tuned weights | Not statistically validated | Feed 53 companies into Random Forest |
| No beta calculation | Missing the core algorithm | Run OLS + RF from spec |
| No macro variables | Misses cycle timing | Add VIX, rates, yield curve |
| No sentiment data | Missing market psychology | Add put/call, AAII, Fear/Greed |
| No compression duration | Can't optimize DTE | Classify: flash/narrative/structural/leverage |

## Iteration History

### Iteration 0: Initial hand-tuned model
- **Method**: min/max normalization, grid-searched weights
- **Weights**: PE_prem=0.45, margin_frag=0.30, cap_ineff=0.10, cash_vuln=0.05, lev=0.10
- **Accuracy**: 58% | Precision: 71% | Recall: 53%
- **Notable**: Correctly separates NVDA/META/MSFT from ZM/DOCU/PTON on live data

### Iteration 1: (NEXT SESSION)
- **Planned**: Feed 53 companies into Random Forest, let it find real betas
- **Planned**: Add moat velocity as a feature
- **Planned**: Dynamic gate based on compression magnitude
- **Target**: 70%+ accuracy, 80%+ precision

## Target Metrics

| Metric | Current | Target v1 | Target v2 | Production |
|--------|---------|-----------|-----------|------------|
| Accuracy | 58% | 70% | 80% | 85%+ |
| Precision | 71% | 80% | 85% | 90%+ |
| Recall | 53% | 65% | 75% | 80%+ |
| R-squared | N/A | 0.60+ | 0.75+ | 0.80+ |
| ZM simulation ROI | 310% (1 trade) | 500%+ (rolling) | 800%+ | - |
| False positive rate | 29% | 20% | 15% | 10% |
