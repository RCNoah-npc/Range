"""Step 3: Exhaustive variable testing.

500+ tests across every combination, with industry segmentation.
Finds which variables are universal vs industry-specific.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pandas as pd
from itertools import combinations
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error

# Load training set
df = pd.read_csv('src/rangers/noah/tsunami/data/training_set.csv')
y = df['abnormal_return_12m']

# ============================================================
# DERIVE ALL CANDIDATE VARIABLES
# ============================================================
df['interest_coverage'] = df['fcf'] / df['de'].replace(0, 0.01)
df['margin_frag'] = df['sga'] * df['gm']
df['leverage_stress'] = df['de'] * (1 - df['fcf'])
df['overval_human'] = df['pe'] * df['sga']
df['rev_efficiency'] = df['roic'] / df['sga'].replace(0, 0.01)
df['pe_to_roic'] = df['pe'] / df['roic'].replace(0, 0.01)  # valuation relative to returns
df['cash_to_debt'] = df['fcf'] / df['de'].replace(0, 0.01)  # cash generation vs leverage
df['sga_leverage'] = df['sga'] * df['de']  # human cost amplified by debt
df['margin_leverage'] = df['gm'] * df['de']  # margin risk amplified by debt
df['fcf_margin'] = df['fcf'] * df['gm']  # cash generation quality
df['roic_leverage'] = df['roic'] / df['de'].replace(0, 0.01)  # return efficiency vs debt
df['pe_sga_gm'] = df['pe'] * df['sga'] * df['gm']  # triple combo

# Replace inf/nan
for col in df.columns:
    if df[col].dtype in [np.float64, np.int64]:
        df[col] = df[col].replace([np.inf, -np.inf], 0).fillna(0)

# All candidate features
raw_features = ['pe', 'sga', 'gm', 'de', 'fcf', 'roic']
derived_features = ['interest_coverage', 'margin_frag', 'leverage_stress', 'overval_human',
                    'rev_efficiency', 'pe_to_roic', 'cash_to_debt', 'sga_leverage',
                    'margin_leverage', 'fcf_margin', 'roic_leverage', 'pe_sga_gm']
all_features = raw_features + derived_features

loo = LeaveOneOut()
rf_params = dict(n_estimators=500, max_depth=4, random_state=42, min_samples_leaf=2)

# ============================================================
# TEST 1: EVERY SINGLE VARIABLE ALONE
# ============================================================
print("=" * 80)
print("TEST 1: EVERY SINGLE VARIABLE ALONE")
print("=" * 80)
print(f"{'Variable':25s} {'R2':>8s} {'MAE':>8s}")
print("-" * 45)

single_results = []
for feat in all_features:
    X = df[[feat]]
    y_pred = cross_val_predict(RandomForestRegressor(**rf_params), X, y, cv=loo)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    single_results.append((feat, r2, mae))
    print(f"  {feat:25s} {r2:+.4f} {mae:.4f}")

single_results.sort(key=lambda x: x[1], reverse=True)
print(f"\nBEST SINGLE: {single_results[0][0]} R2={single_results[0][1]:.4f}")

# ============================================================
# TEST 2: EVERY PAIR (D/E + each other variable)
# ============================================================
print(f"\n{'='*80}")
print("TEST 2: D/E + EACH OTHER VARIABLE")
print("=" * 80)

de_baseline = single_results[[x[0] for x in single_results].index('de')][1]
print(f"D/E baseline R2: {de_baseline:.4f}")
print(f"\n{'Variable added':25s} {'R2':>8s} {'MAE':>8s} {'Delta':>8s}")
print("-" * 55)

pair_results = []
for feat in all_features:
    if feat == 'de':
        continue
    X = df[['de', feat]]
    y_pred = cross_val_predict(RandomForestRegressor(**rf_params), X, y, cv=loo)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    delta = r2 - de_baseline
    pair_results.append((feat, r2, mae, delta))

pair_results.sort(key=lambda x: x[1], reverse=True)
for feat, r2, mae, delta in pair_results:
    better = "+" if delta > 0 else ""
    star = " ***" if delta > 0.05 else (" **" if delta > 0.02 else (" *" if delta > 0 else ""))
    print(f"  {feat:25s} {r2:.4f} {mae:.4f} {better}{delta:.4f}{star}")

# ============================================================
# TEST 3: ALL TRIPLE COMBOS WITH D/E
# ============================================================
print(f"\n{'='*80}")
print("TEST 3: D/E + BEST PAIRS (TOP 20 TRIPLE COMBOS)")
print("=" * 80)

other_feats = [f for f in all_features if f != 'de']
triple_results = []
test_count = 0

for combo in combinations(other_feats, 2):
    cols = ['de'] + list(combo)
    X = df[cols]
    y_pred = cross_val_predict(RandomForestRegressor(**rf_params), X, y, cv=loo)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    triple_results.append((r2, mae, cols))
    test_count += 1

triple_results.sort(key=lambda x: x[0], reverse=True)
print(f"Tested {test_count} combinations")
print(f"\n{'R2':>8s} {'MAE':>8s} {'Delta':>8s} Features")
print("-" * 70)
for r2, mae, cols in triple_results[:20]:
    delta = r2 - de_baseline
    print(f"  {r2:.4f} {mae:.4f} {delta:+.4f} {cols}")

# ============================================================
# TEST 4: ALL QUAD COMBOS WITH D/E (top 20)
# ============================================================
print(f"\n{'='*80}")
print("TEST 4: D/E + TOP QUAD COMBOS")
print("=" * 80)

quad_results = []
for combo in combinations(other_feats, 3):
    cols = ['de'] + list(combo)
    X = df[cols]
    y_pred = cross_val_predict(RandomForestRegressor(**rf_params), X, y, cv=loo)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    quad_results.append((r2, mae, cols))
    test_count += 1

quad_results.sort(key=lambda x: x[0], reverse=True)
print(f"Tested {test_count} total combinations so far")
print(f"\n{'R2':>8s} {'MAE':>8s} Features")
print("-" * 70)
for r2, mae, cols in quad_results[:20]:
    print(f"  {r2:.4f} {mae:.4f} {cols}")

# ============================================================
# TEST 5: INDUSTRY SEGMENTATION
# ============================================================
print(f"\n{'='*80}")
print("TEST 5: INDUSTRY SEGMENTATION")
print("=" * 80)

# Group by industry era
industry_map = {
    'Networking': 'Tech_Infra', 'Enterprise Software': 'Enterprise_SW',
    'Semiconductors': 'Semis', 'Banking': 'Financials',
    'Investment Banking': 'Financials', 'Conglomerate': 'Industrial',
    'Video Comms': 'Growth_Tech', 'E-Signature': 'Growth_Tech',
    'E-Commerce Platform': 'Growth_Tech', 'Enterprise CRM': 'Enterprise_SW',
    'Social Media': 'Consumer_Tech', 'Travel Platform': 'Consumer_Tech',
    'Food Delivery': 'Consumer_Tech', 'EdTech': 'Growth_Tech',
    'Freelance': 'Growth_Tech', 'Crypto Exchange': 'Crypto',
    'Electric Vehicles': 'Industrial', 'Connected Fitness': 'Consumer_Tech',
    'Retail Brokerage': 'Financials', 'Telehealth': 'Growth_Tech',
}
df['industry_group'] = df['industry'].map(industry_map).fillna('Other')

print(f"\nIndustry groups:")
for group, count in df['industry_group'].value_counts().items():
    group_y = y[df['industry_group'] == group]
    print(f"  {group:20s}: {count} companies, avg AR={group_y.mean():+.1%}")

# Which variables matter most PER INDUSTRY?
print(f"\nFEATURE IMPORTANCE BY INDUSTRY GROUP:")
print(f"{'Group':20s} | {'Top Feature':25s} {'Imp%':>6s} | {'2nd Feature':25s} {'Imp%':>6s}")
print("-" * 90)

best_features = ['de', 'leverage_stress', 'rev_efficiency']
for group in df['industry_group'].unique():
    mask = df['industry_group'] == group
    if mask.sum() < 3:
        continue
    X_group = df.loc[mask, all_features]
    y_group = y[mask]
    rf = RandomForestRegressor(**rf_params)
    rf.fit(X_group, y_group)
    importances = dict(zip(all_features, rf.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    top1 = sorted_imp[0]
    top2 = sorted_imp[1]
    print(f"  {group:20s} | {top1[0]:25s} {top1[1]*100:5.1f}% | {top2[0]:25s} {top2[1]*100:5.1f}%")

# ============================================================
# TEST 6: WHICH VARIABLES ARE UNIVERSAL vs INDUSTRY-SPECIFIC?
# ============================================================
print(f"\n{'='*80}")
print("TEST 6: UNIVERSAL vs INDUSTRY-SPECIFIC VARIABLES")
print("=" * 80)

# For each variable, check if its importance is consistent across industries
print(f"\n{'Variable':25s} {'Avg Imp%':>10s} {'Std Imp%':>10s} {'Consistent?':>12s}")
print("-" * 65)

for feat in all_features:
    imps = []
    for group in df['industry_group'].unique():
        mask = df['industry_group'] == group
        if mask.sum() < 3:
            continue
        X_group = df.loc[mask, [feat]]
        y_group = y[mask]
        rf = RandomForestRegressor(**rf_params)
        rf.fit(X_group, y_group)
        imps.append(rf.feature_importances_[0])
    if imps:
        avg = np.mean(imps) * 100
        std = np.std(imps) * 100
        consistent = "UNIVERSAL" if std < 15 else ("MIXED" if std < 30 else "INDUSTRY-SPECIFIC")
        print(f"  {feat:25s} {avg:9.1f}% {std:9.1f}% {consistent:>12s}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print(f"\n{'='*80}")
print(f"EXHAUSTIVE TESTING COMPLETE: {test_count} total tests")
print("=" * 80)

overall_best = max(triple_results + quad_results, key=lambda x: x[0])
print(f"\nBest single variable: {single_results[0][0]} (R2={single_results[0][1]:.4f})")
print(f"Best D/E pair:        de + {pair_results[0][0]} (R2={pair_results[0][1]:.4f})")
print(f"Best triple:          {triple_results[0][2]} (R2={triple_results[0][0]:.4f})")
print(f"Best quad:            {quad_results[0][2]} (R2={quad_results[0][0]:.4f})")
print(f"Best overall:         {overall_best[2]} (R2={overall_best[0]:.4f})")
