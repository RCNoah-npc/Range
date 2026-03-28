"""Step 2: Run OLS regression + Random Forest on the training set.

This is the REAL algorithm from the spec:
AR_t = α + Σ(β_i × V_i) + Σ(γ_j × F_j) + ε

Let the DATA find the weights.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error

# ============================================================
# LOAD TRAINING SET
# ============================================================
data_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'rangers', 'noah', 'tsunami', 'data', 'training_set.csv')
df = pd.read_csv(data_path)
print(f"Loaded {len(df)} companies from training set")
print()

# ============================================================
# DEFINE FEATURES AND TARGET
# ============================================================
features = ['pe', 'sga', 'gm', 'de', 'fcf', 'roic']
target = 'abnormal_return_12m'

X = df[features].copy()
y = df[target].copy()

# Handle any NaN/inf
X = X.fillna(0)
y = y.fillna(0)

print("FEATURE STATISTICS:")
print(X.describe().round(3))
print(f"\nTarget (AR_12M) stats:")
print(f"  mean={y.mean():.3f}, std={y.std():.3f}, min={y.min():.3f}, max={y.max():.3f}")

# ============================================================
# PHASE 1: OLS REGRESSION (Statistical Significance)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 1: OLS REGRESSION")
print("=" * 70)

X_ols = sm.add_constant(X)
model_ols = sm.OLS(y, X_ols).fit()
print(model_ols.summary())

print("\nKEY METRICS:")
print(f"  R-squared:     {model_ols.rsquared:.4f}")
print(f"  Adj R-squared: {model_ols.rsquared_adj:.4f}")
print(f"  F-statistic:   {model_ols.fvalue:.4f} (p={model_ols.f_pvalue:.4f})")

print("\nCOEFFICIENTS (beta weights from regression):")
for feat, coef, pval in zip(['const'] + features, model_ols.params, model_ols.pvalues):
    sig = "***" if pval < 0.01 else ("**" if pval < 0.05 else ("*" if pval < 0.10 else ""))
    print(f"  {feat:12s}: B={coef:+.4f}  p-value={pval:.4f} {sig}")

print("\nINTERPRETATION:")
for feat, coef, pval in zip(features, model_ols.params[1:], model_ols.pvalues[1:]):
    if pval < 0.10:
        direction = "more negative AR" if coef < 0 else "less negative AR"
        print(f"  {feat}: 1 unit increase -> {coef:+.2%} abnormal return ({direction})")
    else:
        print(f"  {feat}: NOT statistically significant (p={pval:.3f})")

# ============================================================
# PHASE 2: RANDOM FOREST (Non-linear Feature Importance)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 2: RANDOM FOREST REGRESSOR")
print("=" * 70)

rf = RandomForestRegressor(n_estimators=1000, max_depth=5, random_state=42, min_samples_leaf=2)
rf.fit(X, y)

# In-sample R-squared
y_pred_rf = rf.predict(X)
r2_rf = r2_score(y, y_pred_rf)
mae_rf = mean_absolute_error(y, y_pred_rf)
print(f"In-sample R-squared:       {r2_rf:.4f}")
print(f"In-sample MAE:             {mae_rf:.4f}")

# Leave-One-Out Cross Validation (proper out-of-sample test for small datasets)
print("\nRunning Leave-One-Out Cross Validation...")
loo = LeaveOneOut()
y_pred_loo = cross_val_predict(
    RandomForestRegressor(n_estimators=500, max_depth=4, random_state=42, min_samples_leaf=2),
    X, y, cv=loo
)
r2_loo = r2_score(y, y_pred_loo)
mae_loo = mean_absolute_error(y, y_pred_loo)
print(f"LOO CV R-squared:          {r2_loo:.4f}")
print(f"LOO CV MAE:                {mae_loo:.4f}")

# Feature importance
importances = rf.feature_importances_
imp_df = pd.DataFrame({
    'Variable': features,
    'Importance_Pct': importances * 100
}).sort_values('Importance_Pct', ascending=False)

print("\nFEATURE IMPORTANCE (Random Forest - what actually predicts drops):")
for _, row in imp_df.iterrows():
    bar = "#" * int(row['Importance_Pct'] * 2)
    print(f"  {row['Variable']:12s}: {row['Importance_Pct']:5.1f}% [{bar}]")

# ============================================================
# PHASE 3: GRADIENT BOOSTING (comparison)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3: GRADIENT BOOSTING REGRESSOR")
print("=" * 70)

gb = GradientBoostingRegressor(n_estimators=500, max_depth=3, learning_rate=0.05, random_state=42, min_samples_leaf=2)
gb.fit(X, y)

y_pred_gb = gb.predict(X)
r2_gb = r2_score(y, y_pred_gb)
print(f"In-sample R-squared:       {r2_gb:.4f}")

y_pred_gb_loo = cross_val_predict(
    GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42, min_samples_leaf=2),
    X, y, cv=loo
)
r2_gb_loo = r2_score(y, y_pred_gb_loo)
mae_gb_loo = mean_absolute_error(y, y_pred_gb_loo)
print(f"LOO CV R-squared:          {r2_gb_loo:.4f}")
print(f"LOO CV MAE:                {mae_gb_loo:.4f}")

gb_imp = pd.DataFrame({
    'Variable': features,
    'Importance_Pct': gb.feature_importances_ * 100
}).sort_values('Importance_Pct', ascending=False)

print("\nFEATURE IMPORTANCE (Gradient Boosting):")
for _, row in gb_imp.iterrows():
    bar = "#" * int(row['Importance_Pct'] * 2)
    print(f"  {row['Variable']:12s}: {row['Importance_Pct']:5.1f}% [{bar}]")

# ============================================================
# COMPARISON: ACTUAL vs PREDICTED for each company
# ============================================================
print("\n" + "=" * 70)
print("PREDICTIONS vs ACTUALS (Random Forest LOO)")
print("=" * 70)
print(f"{'Ticker':8s} {'Actual':>8s} {'Predicted':>10s} {'Error':>8s} {'Recov':>6s}")
print("-" * 48)

for i, row in df.iterrows():
    actual = row[target]
    predicted = y_pred_loo[i]
    error = predicted - actual
    recov = "YES" if row["recovered"] else "no"
    print(f"{row['ticker']:8s} {actual:+7.1%} {predicted:+9.1%} {error:+7.1%} {recov:>6s}")

# ============================================================
# SAVE THE MODEL WEIGHTS
# ============================================================
print("\n" + "=" * 70)
print("MODEL COMPARISON SUMMARY")
print("=" * 70)
print(f"{'Model':25s} {'In-Sample R²':>15s} {'LOO CV R²':>12s} {'LOO MAE':>10s}")
print("-" * 65)
print(f"{'OLS Regression':25s} {model_ols.rsquared:>14.4f} {'N/A':>12s} {'N/A':>10s}")
print(f"{'Random Forest':25s} {r2_rf:>14.4f} {r2_loo:>11.4f} {mae_loo:>9.4f}")
print(f"{'Gradient Boosting':25s} {r2_gb:>14.4f} {r2_gb_loo:>11.4f} {mae_gb_loo:>9.4f}")

# Save weights
weights_output = os.path.join(os.path.dirname(__file__), '..', 'src', 'rangers', 'noah', 'tsunami', 'data', 'model_weights_v1.csv')
imp_df.to_csv(weights_output, index=False)
print(f"\nRandom Forest weights saved to {weights_output}")

# OLS coefficients
ols_output = os.path.join(os.path.dirname(__file__), '..', 'src', 'rangers', 'noah', 'tsunami', 'data', 'ols_coefficients_v1.csv')
ols_df = pd.DataFrame({
    'variable': ['const'] + features,
    'coefficient': model_ols.params,
    'p_value': model_ols.pvalues,
    'significant': ['***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else '' for p in model_ols.pvalues]
})
ols_df.to_csv(ols_output, index=False)
print(f"OLS coefficients saved to {ols_output}")
