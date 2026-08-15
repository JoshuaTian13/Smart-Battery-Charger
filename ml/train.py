from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit

from features import FEATURE_NAMES, PHASE_CODES


def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "cycle_id",
        "cycle_count",
        "voltage_v",
        "current_ma",
        "temperature_c",
        "phase",
        "delivered_capacity_mah",
        "health_pct",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    phase_codes = frame["phase"].map(PHASE_CODES)
    prepared = pd.DataFrame(
        {
            "cycle_id": frame["cycle_id"].to_numpy(copy=True),
            "cycle_count": frame["cycle_count"].to_numpy(copy=True),
            "voltage_v": frame["voltage_v"].to_numpy(copy=True),
            "current_ma": frame["current_ma"].to_numpy(copy=True),
            "temperature_c": frame["temperature_c"].to_numpy(copy=True),
            "phase": frame["phase"].to_numpy(copy=True),
            "delivered_capacity_mah": frame["delivered_capacity_mah"].to_numpy(
                copy=True
            ),
            "health_pct": frame["health_pct"].to_numpy(copy=True),
            "power_w": (
                frame["voltage_v"].to_numpy(copy=True)
                * frame["current_ma"].to_numpy(copy=True)
                / 1_000.0
            ),
            "phase_code": phase_codes.to_numpy(copy=True),
        }
    )
    if prepared["phase_code"].isna().any():
        raise ValueError("dataset contains an unknown charge phase")
    prepared = prepared.dropna(subset=FEATURE_NAMES + ["health_pct", "cycle_id"])
    return prepared


def train(dataset: Path, output_dir: Path) -> dict[str, float | str]:
    frame = prepare_frame(pd.read_csv(dataset))
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=17)
    train_index, test_index = next(
        split.split(
            frame[FEATURE_NAMES].to_numpy(),
            frame["health_pct"],
            groups=frame["cycle_id"],
        )
    )
    train_frame = frame.iloc[train_index]
    test_frame = frame.iloc[test_index]

    folds = GroupKFold(n_splits=5)
    candidates = {
        "gradient_boosting": (
            GradientBoostingRegressor(random_state=17),
            {
                "n_estimators": [100, 200],
                "learning_rate": [0.03, 0.1],
                "max_depth": [2, 3],
            },
        ),
        "random_forest": (
            RandomForestRegressor(
                random_state=17,
                n_jobs=1,
            ),
            {
                "n_estimators": [100, 200],
                "max_depth": [5, 10, None],
                "min_samples_leaf": [1, 3],
            },
        ),
    }

    searches: dict[str, GridSearchCV] = {}
    for name, (pipeline, grid) in candidates.items():
        search = GridSearchCV(
            pipeline,
            grid,
            scoring="neg_mean_absolute_error",
            cv=folds,
            n_jobs=1,
            refit=True,
        )
        search.fit(
            train_frame[FEATURE_NAMES].to_numpy(),
            train_frame["health_pct"],
            groups=train_frame["cycle_id"],
        )
        searches[name] = search

    selected_name, selected = max(
        searches.items(),
        key=lambda pair: pair[1].best_score_,
    )
    predictions = selected.predict(test_frame[FEATURE_NAMES].to_numpy())
    metrics: dict[str, float | str] = {
        "selected_model": selected_name,
        "cross_validated_mae": round(-float(selected.best_score_), 4),
        "holdout_mae": round(
            float(mean_absolute_error(test_frame["health_pct"], predictions)),
            4,
        ),
        "holdout_r2": round(
            float(r2_score(test_frame["health_pct"], predictions)),
            4,
        ),
        "training_rows": float(len(train_frame)),
        "holdout_rows": float(len(test_frame)),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": selected.best_estimator_,
        "feature_names": FEATURE_NAMES,
        "metrics": metrics,
    }
    joblib.dump(bundle, output_dir / "model.joblib")
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the advisory battery-health model")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts"))
    args = parser.parse_args()
    print(json.dumps(train(args.dataset, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
