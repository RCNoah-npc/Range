"""
Phase 4: Model Training
Gradient boosted trees with time-series cross-validation.
No lookahead bias. Expanding window CV.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    classification_report, precision_recall_curve
)
from sklearn.model_selection import TimeSeriesSplit


def prepare_training_data(feature_sets: dict[str, pd.DataFrame]) -> tuple:
    """Combine all stocks into single training set, sorted by date."""
    frames = []
    for ticker, df in feature_sets.items():
        df = df.copy()
        df["_ticker"] = ticker
        frames.append(df)

    if not frames:
        raise ValueError("No training data available")

    combined = pd.concat(frames).sort_index()

    # Feature columns (exclude target and metadata)
    exclude = {"target", "target_multiclass", "_ticker"}
    feature_cols = [c for c in combined.columns if c not in exclude]

    X = combined[feature_cols]
    y = combined["target"]
    tickers = combined["_ticker"]
    dates = combined.index

    return X, y, tickers, dates, feature_cols


def time_series_split(X, y, dates, n_splits=5):
    """Expanding window time-series split."""
    unique_dates = sorted(dates.unique())
    n = len(unique_dates)

    splits = []
    for i in range(n_splits):
        # Train on first (i+1)/(n_splits+1) of data
        train_end_idx = int(n * (i + 1) / (n_splits + 1))
        test_start_idx = train_end_idx
        test_end_idx = int(n * (i + 2) / (n_splits + 1))

        train_end = unique_dates[min(train_end_idx, n - 1)]
        test_start = unique_dates[min(test_start_idx, n - 1)]
        test_end = unique_dates[min(test_end_idx, n - 1)]

        train_mask = dates <= train_end
        test_mask = (dates > test_start) & (dates <= test_end)

        if train_mask.sum() > 100 and test_mask.sum() > 20:
            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]
            splits.append((train_idx, test_idx))

    return splits


def train_and_evaluate(feature_sets: dict[str, pd.DataFrame]) -> tuple:
    """Train gradient boosted classifier with time-series CV."""
    X, y, tickers, dates, feature_cols = prepare_training_data(feature_sets)

    print(f"  Training data: {X.shape[0]} rows, {X.shape[1]} features")
    print(f"  Class balance: {y.value_counts().to_dict()}")

    # Handle NaN values for HistGradientBoosting (it handles them natively)
    # Time-series cross-validation
    splits = time_series_split(X, y, dates, n_splits=5)

    cv_metrics = []
    feature_importances = np.zeros(len(feature_cols))

    for fold, (train_idx, test_idx) in enumerate(splits):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        clf = HistGradientBoostingClassifier(
            max_depth=5,
            learning_rate=0.05,
            max_iter=300,
            min_samples_leaf=20,
            l2_regularization=1.0,
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred

        # Precision at top decile (most important metric)
        top_decile_idx = np.argsort(y_prob)[-max(1, len(y_prob) // 10):]
        precision_top_decile = y_test.iloc[top_decile_idx].mean()

        metrics = {
            "fold": fold,
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "precision_top_decile": precision_top_decile,
            "n_train": len(train_idx),
            "n_test": len(test_idx),
        }
        cv_metrics.append(metrics)
        print(f"  Fold {fold}: P={metrics['precision']:.3f} R={metrics['recall']:.3f} "
              f"F1={metrics['f1']:.3f} P@top10%={precision_top_decile:.3f}")

    # Train final model on all data
    final_model = HistGradientBoostingClassifier(
        max_depth=5,
        learning_rate=0.05,
        max_iter=300,
        min_samples_leaf=20,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=42,
    )
    final_model.fit(X, y)

    # Feature importance
    importances = pd.Series(
        final_model.feature_importances_ if hasattr(final_model, "feature_importances_") else np.zeros(len(feature_cols)),
        index=feature_cols
    ).sort_values(ascending=False)

    avg_metrics = {
        "avg_precision": np.mean([m["precision"] for m in cv_metrics]),
        "avg_recall": np.mean([m["recall"] for m in cv_metrics]),
        "avg_f1": np.mean([m["f1"] for m in cv_metrics]),
        "avg_precision_top_decile": np.mean([m["precision_top_decile"] for m in cv_metrics]),
        "cv_folds": cv_metrics,
        "feature_importances": importances.head(20).to_dict(),
        "feature_cols": feature_cols,
    }

    print(f"\n  ═══ Model Summary ═══")
    print(f"  Avg Precision: {avg_metrics['avg_precision']:.3f}")
    print(f"  Avg Recall:    {avg_metrics['avg_recall']:.3f}")
    print(f"  Avg F1:        {avg_metrics['avg_f1']:.3f}")
    print(f"  Avg P@Top10%:  {avg_metrics['avg_precision_top_decile']:.3f}")
    print(f"  Top features:  {list(importances.head(5).index)}")

    return final_model, avg_metrics
