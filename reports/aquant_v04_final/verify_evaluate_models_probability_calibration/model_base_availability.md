# Model Base Availability

This table records whether each model base is actually importable in the local environment. Missing optional packages must be reported and may only fall back with an explicit registry reason.

| model_base_id | package | available | version | role | fallback_policy |
|---|---|---:|---|---|---|
| factor_score | builtin | True | builtin | transparent_baseline | none |
| sklearn_linear | sklearn | True | 1.6.1 | logistic_ridge_linear_baseline | fallback_to_factor_score_with_registry_reason |
| lightgbm | lightgbm | True | 4.6.0 | gbdt_classifier_regressor_ranker | fallback_to_sklearn_or_factor_score_with_registry_reason |
| xgboost | xgboost | True | 3.2.0 | gbdt_challenger | fallback_to_factor_score_with_registry_reason |
| catboost | catboost | True | 1.2.10 | gbdt_challenger | fallback_to_factor_score_with_registry_reason |