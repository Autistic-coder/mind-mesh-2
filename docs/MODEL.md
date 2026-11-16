# Model training and data documentation

## Dataset validation

`model/train.py` requires all six features and the binary `Machine failure` target, rejects missing required values, validates Type as exactly L/M/H, ensures at least 1,000 rows, and prevents leakage columns from entering the feature list. The raw CSV SHA-256 is `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`.

## Reproducible methodology

- Fixed random seed: 42.
- Stratified split: 7,000 train / 1,500 validation / 1,500 test.
- OneHotEncoder for Type inside a ColumnTransformer.
- RandomForestClassifier: 500 trees, minimum leaf size 2, `balanced_subsample` class weights, one deterministic job.
- Threshold selected by validation F1 with recall as the tie-breaker: 0.36.
- Test set evaluated once after selection.

The complete Pipeline is stored at `model/mindmesh_rf_v1.joblib`; `model/model_manifest.json` is the authoritative generated evidence. Do not edit results by hand.

## Actual result

Accuracy 0.9780, precision 0.6607, recall 0.7255, F1 0.6916 and ROC–AUC 0.9768. The matrix is 1,430 true normals, 19 false alarms, 14 missed failures and 37 detected failures. The always-normal baseline reaches 0.966 accuracy but 0 recall.

## Intentional retraining

```powershell
python .\model\train.py --data .\data\raw\ai4i2020.csv --output .\model
```

Review the new manifest and tests before replacing a released artifact. A changed artifact requires a new model version and application release.

## Limitations

AI4I is synthetic, class imbalance is severe, accepted ranges are dataset-derived, and probability calibration is not guaranteed for a real plant. A prediction is decision support—not a safe-operating declaration, causal explanation or maintenance instruction.

