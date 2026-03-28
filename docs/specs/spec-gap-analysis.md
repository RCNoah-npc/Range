# Spec Gap Analysis: PDF Algorithm vs What We Built

## The PDF's Prescribed Sequence

The spec defines a strict phased approach. Here's exactly what it says to do, in order:

### Phase 1: Structure the Variables (p1)
**Spec says:**
- Vulnerability Metrics: SGA%, Gross Margin, Intangible Asset Ratio
- Financial Strength Metrics: FCF Yield, ROIC, Debt-to-Equity & Interest Coverage
- Macro/Industry: HHI (market concentration), Sector Beta

**We built:** SGA%, Gross Margin, FCF Yield, ROIC, D/E
**GAPS:**
- [ ] Missing: Intangible Asset Ratio (IP-heavy vs hard assets)
- [ ] Missing: Interest Coverage Ratio (can they service debt?)
- [ ] Missing: HHI (Herfindahl-Hirschman Index for market concentration)
- [ ] Missing: Sector Beta (stock volatility relative to market)

### Phase 2: Mathematical Framework (p1-2)
**Spec says:**
Multiple Linear Regression baseline:
```
AR_t = α + Σ(β_i × V_i) + Σ(γ_j × F_j) + ε
```
- AR_t = Abnormal Return over timeframe t
- α = Intercept (baseline drift)
- β_i = CALCULATED weight for each Vulnerability metric
- γ_j = CALCULATED weight for each Financial Strength metric
- ε = Error term

Then upgrade to Random Forest / Gradient Boosting for non-linear thresholds.

**We built:** Hand-tuned weights with grid search. No regression. No abnormal return calculation.
**GAPS:**
- [ ] Never calculated abnormal returns (stock return minus S&P 500 return)
- [ ] Never ran OLS regression to get β and γ coefficients
- [ ] Never calculated p-values to check statistical significance
- [ ] Random Forest exists in code but only fed 10 companies, not 53
- [ ] No R-squared calculation
- [ ] No feature importance extraction from the actual model

### Phase 3: Backtesting Protocol (p2-3)
**Spec says:**
1. Set T-Zero Event (ChatGPT launch = Nov 2022 for AI cohort)
2. Snapshot the Metrics: Feed financials as they were BEFORE T-Zero
3. Run Forward Window: Measure AR at 3, 6, and 12 months post T-Zero
4. Train the Model: Regression/ML to determine which metrics predict the drop

Patient Zero Cohort: CHGG, FVRR, UPWK, TEP, TASK, SSTK, TWOU, GETY, EPAM, LZB

**We built:** 53-company database with pre-crash fundamentals. BUT:
**GAPS:**
- [ ] Never calculated the 3, 6, 12-month abnormal returns properly
- [ ] Never snapshotted metrics at T-Zero (used approximate pre-crash values)
- [ ] Never ran the regression on this data
- [ ] T-Zero dates are approximate, not precise

### Phase 4: Iterate and Tweak (p2)
**Spec says:**
- Evaluate R-squared (must be > 0.75)
- Prune variables with high p-values (statistically insignificant)
- Add Alternative Data: web traffic, sentiment, employee headcount
- Address Multicollinearity (remove redundant variables)

**We built:** Hand comparison of scores vs outcomes. No R-squared.
**GAPS:**
- [ ] No R-squared tracking
- [ ] No p-value pruning
- [ ] No multicollinearity check (Operating Margin and Gross Margin overlap?)
- [ ] Alternative data not integrated

### Phase 5: Variable Delta Dataset (p5)
**Spec says:**
Track the VELOCITY of change (delta) in vulnerability metrics pre/post T-Zero:
```
v = (V_T0 - V_T-1) / V_T-1
```
Use Primary_Delta_Pct and Secondary_Delta_Pct as features.

**We built:** Nothing. This is the "moat velocity" concept we discussed.
**GAPS:**
- [ ] No delta calculation implemented
- [ ] No pre/post T-Zero metric comparison
- [ ] This is the single biggest gap -- spec says deltas predict better than static values

### Phase 6: Forward Prediction Equation (p7)
**Spec says:**
```
E[AR_12M] = α + Σ(β_i × δ_hat_i) + Σ(γ_j × M_j) + ε
```
- δ_hat_i = Estimated Operational Shock (YOUR estimate of how much damage)
- M_j = Current Moat Metric (real-time financial defense data)
- Must run through Monte Carlo simulation (base, bear, severe cases)

**We built:** Simple `projected_price = EPS × (1-decay) × terminal_PE`. No Monte Carlo.
**GAPS:**
- [ ] No Monte Carlo simulation for confidence intervals
- [ ] No base/bear/severe scenario matrix
- [ ] Prediction equation not using regression-derived weights
- [ ] No confidence levels on predictions

### Phase 7: Sensitivity Matrix (p9)
**Spec says:**
Stress test across three shock scenarios:
- Base Case: moderate market share loss
- Bear Case: 1.5× worse than expected
- Severe Case: 2.5× worse (terminal velocity)

**We built:** Nothing.
**GAPS:**
- [ ] No sensitivity matrix
- [ ] No scenario stress testing
- [ ] No worst/base/best case outputs

### Phase 8: Options Underwriting (p12-13)
**Spec says:**
1. IV Rank Filter: reject if IV too high
2. Strike Selection: map to Base Case Impact
3. Payoff Ratio: must yield 300%+ ROP
4. VRP calculation: `VRP = IV_current - HV_historical`

**We built:** VRP filter, strike selection, ROP gate -- these are done.
**STATUS:** Mostly complete. Missing IV Rank (requires paid data).

### Phase 9: Market Pressure Overlay (p14-15)
**Spec says:**
1. Volatility Skew (25-delta put IV vs call IV)
2. Put/Call Volume Ratio
3. Net Gamma Exposure (GEX)
4. Dark Pool / Off-Exchange Short Volume

**We built:** Spec'd in variable universe but not implemented.
**GAPS:**
- [ ] No volatility skew calculation
- [ ] Put/call ratio not pulled from live data
- [ ] No gamma exposure tracking
- [ ] No dark pool volume tracking

### Phase 10: Kelly Sizing (p32-33)
**Spec says:**
```
f* = p - (q / b)
```
Applied at Quarter-Kelly with 5% max cap per position.

**We built:** This is done. Changed to 10% cap per user request.
**STATUS:** Complete.

### Phase 11: Database Schema (p16-18)
**Spec says:** PostgreSQL with 4 tables + views
**We built:** SQLite with 6 tables
**STATUS:** Complete (SQLite is the planned starting point).

---

## Priority Fix Order (following the spec's sequence)

The spec is clear: you MUST get Phase 2-3 right before anything else works. The regression weights feed everything downstream.

### Step 1: Calculate Abnormal Returns (Phase 3)
For each of the 53 companies, calculate:
```
AR_12M = (stock_return_12M) - (SP500_return_12M)
```
This is the target variable Y for the regression.

### Step 2: Run the Regression (Phase 2)
Feed the 53 companies with their pre-crash fundamentals (X) and abnormal returns (Y) into:
1. OLS → check p-values, get R-squared
2. Random Forest → get feature importances

### Step 3: Extract Real Weights
The regression output IS the model. β_i tells you exactly how much each variable contributes.

### Step 4: Add Deltas (Phase 5)
Calculate the velocity of change in each metric. This is the "moat velocity" concept.

### Step 5: Build the Forward Equation (Phase 6)
Use the extracted weights to predict new companies.

### Step 6: Monte Carlo / Sensitivity (Phase 7)
Run base/bear/severe scenarios. This gives confidence intervals.

### Step 7: Dashboard
Only THEN build the dashboard showing all of the above.

---

## Summary: What We Skipped

We jumped from Phase 1 (variables) directly to hand-tuned scoring and dashboard building. We skipped:
- The actual regression (Phase 2)
- Proper backtesting with abnormal returns (Phase 3)
- Variable pruning and iteration (Phase 4)
- Delta/velocity calculation (Phase 5)
- Forward prediction equation (Phase 6)
- Monte Carlo sensitivity (Phase 7)

The hand-tuned model at 58% accuracy is what you get without the real math. The spec's approach should push this significantly higher because it lets the DATA determine what matters, not our guesses.
