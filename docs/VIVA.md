# Viva questions and short answers

1. **Why Random Forest?** It handles nonlinear interactions, mixed transformed inputs and imbalance controls well while remaining reproducible and inspectable.
2. **Why a Pipeline?** It binds categorical preprocessing and inference to the estimator so training and production cannot silently use different transformations.
3. **Why exclude TWF/HDF/PWF/OSF/RNF?** They encode failure modes and leak the target outcome.
4. **Why stratify splits?** Failures are rare; stratification preserves similar class ratios in train, validation and test sets.
5. **Why use validation data for the threshold?** Selecting it on the test set would bias the final reported result.
6. **Why `balanced_subsample`?** Each tree weights the minority failure class using its bootstrap sample, reducing the always-normal bias.
7. **What is recall?** Of actual failures, the proportion the model flags. Here it is 37/51 = 72.55%.
8. **What is precision?** Of flagged machines, the proportion that actually failed. Here it is 37/56 = 66.07%.
9. **What is a false negative?** A failing machine predicted normal; there are 14 in the test set.
10. **Why is accuracy insufficient?** Always predicting normal already achieves 96.6% because failures are rare, but catches none.
11. **What does ROC–AUC mean?** The probability that a random failure ranks above a random normal case across thresholds; measured here as 0.9768.
12. **Does feature importance prove causation?** No. It describes split utility in this fitted model, not a causal mechanism.
13. **How is ownership enforced?** The API derives the user from a server-managed session and filters every query by that user.
14. **Why Argon2id?** It is a modern memory-hard password hash designed to resist password cracking.
15. **Why CSRF protection with cookies?** Browsers automatically attach cookies; a separate unpredictable token proves the intended client flow.
16. **Why SameSite=None in production?** Vercel and Render are different sites, so credentialed API requests need a Secure cross-site session cookie.
17. **Why store a session hash?** A database leak does not directly reveal reusable raw session tokens.
18. **Why not retrain on API startup?** Startup must be deterministic and fast; retraining would change production behaviour and invalidate measured evidence.
19. **How are CSV exports protected?** Values beginning with spreadsheet formula characters are prefixed to prevent execution.
20. **What would you improve next?** Validate on real plant data, monitor drift/calibration, add a shared rate limiter and establish governed retraining.

