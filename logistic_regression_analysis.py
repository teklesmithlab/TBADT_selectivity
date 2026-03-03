from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# load the datasets
literature_molecules = pd.read_csv('raw_data/literature_dataset_just_substrates.csv')
validation_molecules = pd.read_csv('raw_data/validation_dataset.csv')

# define feature and label columns
feature_columns = [
    "ML BDE",
    "NBO Charge",
    "Mulliken Charge",
    "Lowdin Charge",
    "Hirshfeld Charge",
    "Minimum SOMO",
    "Maximum SOMO",
    "Lowest energy SOMO",
    "Average SOMO",
    "Radical Hirshfeld Charge",
    "Minimum electrophilicity",
    "Maximum electrophilicity",
    "Lowest energy electrophilicity",
    "Average electrophilicity",
    "% Vbur H",
    "Shellbur H",
    "% Vbur radical",
    "Shellbur radical",
]

label_column = ["HAT"]

# separate features and labels for both datasets
x_train = literature_molecules[feature_columns]
y_train = literature_molecules[label_column]

x_val = validation_molecules[feature_columns]
y_val = validation_molecules[label_column]

# build the logistic regression model
model = Pipeline(
    steps=[
        ("scaler", StandardScaler()),
        (
            "clf",
            LogisticRegression(
                penalty="l2",
                C=1.0,
                solver="liblinear",
                class_weight="balanced",
                max_iter=10,
                random_state=0,
            ),
        ),
    ]
)

# train on just the literature dataset
model.fit(x_train, y_train)

# validate with the validation dataset
validation_probabilities = model.predict_proba(x_val)[:, 1]  # get the probability of the positive class

print("\n" + "=" * 60)
print("Validation Predictions")
print("=" * 60)

results_df = pd.DataFrame({
    "Predicted Probability": validation_probabilities,
    "True Label": y_val['HAT'],
})

print(results_df.to_string(index=False))

# now for coefficient analysis
coefs = model.named_steps["clf"].coef_.ravel()

# take the natural exponent of coefficients to get their odds ratios
importance = (coefs ** 2) / np.sum(coefs ** 2)

importance_df = (
    pd.DataFrame({
        "Feature": feature_columns,
        "Beta (Coefficient)": coefs,
        "Percent Importance": 100 * importance,
    })
    .sort_values("Percent Importance", ascending=False)
)

print("\n" + "=" * 60)
print("Feature-Level Importance")
print("=" * 60)
print(importance_df.to_string(index=False, float_format="%.3f"))

# group features based on their mechanistic categories
feature_groups = {
    "Hydrogen steric features": ["% Vbur H", "Shellbur H"],
    "Hydrogen electronic features": [
        "NBO Charge",
        "Mulliken Charge",
        "Lowdin Charge",
        "Hirshfeld Charge",
    ],
    "Radical electronic features": [
        "Minimum SOMO",
        "Maximum SOMO",
        "Lowest energy SOMO",
        "Average SOMO",
        "Radical Hirshfeld Charge",
        "Minimum electrophilicity",
        "Maximum electrophilicity",
        "Lowest energy electrophilicity",
        "Average electrophilicity",
    ],
    "Radical steric features": ["% Vbur radical", "Shellbur radical"],
    "BDE": ["ML BDE"],
}

group_importance = {}

for group_name, feats in feature_groups.items():
    mask = importance_df["Feature"].isin(feats)
    group_importance[group_name] = importance_df.loc[
        mask, "Percent Importance"
    ].sum()

# group features by mechanistic category and sum their importance
group_importance_df = (
    pd.DataFrame(
        list(group_importance.items()),
        columns=["Feature Group", "Total Percent Importance"],
    )
    .sort_values("Total Percent Importance", ascending=False)
)

print("\n" + "=" * 60)
print("Grouped Mechanistic Feature Importance")
print("=" * 60)
print(group_importance_df.to_string(index=False, float_format="%.3f"))

print("\n" + "=" * 60)
print("Model Intercept")
print("=" * 60)
print(f"Intercept: {model.named_steps['clf'].intercept_[0]:.4f}")
print("=" * 60)

