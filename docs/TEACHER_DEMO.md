# Teacher demonstration guide

Allow 8–10 minutes.

1. Open Model Report first. Show the 10,000 records, six inputs, dataset hash, fixed split and model v1.0.0 to prove training occurred before deployment.
2. Explain leakage: failure-mode columns reveal the target and Product ID/UDI are identifiers, so none is an input.
3. Compare 97.8% model accuracy with the 96.6% always-normal baseline. Emphasise that the baseline catches zero failures.
4. Show the confusion matrix: 37 detected failures, 14 missed failures and 19 false alarms. Define why missed failures matter.
5. Register a new account and point out protected navigation/session restoration.
6. Run a normal single-machine prediction. Explain probability, risk band, model version, timestamp and recommendation. Say explicitly that probability is not certainty.
7. Download the batch template, upload valid rows, show distribution and download the formula-safe results.
8. Open history, inspect a record, filter it and explain account ownership enforcement.
9. Open Ask MindMesh. Demonstrate labelled static help or explicitly opt in to sharing one prediction summary.
10. Log out, sign in to a second account and show that the first account's predictions and conversations are absent.

Finish with limitations: synthetic data, rare failures, dataset-derived ranges and no replacement for inspection.

