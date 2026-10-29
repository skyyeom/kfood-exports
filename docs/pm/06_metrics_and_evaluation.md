# 06 — Metrics & Evaluation Plan

## 1. Metric tree
```
North star: Time to a defensible TOP3 (< 5 min median)
├── Speed
│   ├── Re-rank latency p95 ≤ 500 ms
│   ├── Agent first token ≤ 5 s (warm)
│   └── Report generation ≤ 60 s
├── Defensibility (quality of the answer)
│   ├── Data: provenance coverage = 100% of displayed numbers
│   ├── Method: TOP3 robustness reported (P(TOP3)), TOPSIS agreement
│   ├── Agent: numeric faithfulness ≥ 95%, citation precision ≥ 90%, refusal accuracy ≥ 90%
│   ├── RAG: hit@5 ≥ 85%
│   └── Forecast: beats naïve in ≥ 60% of series (MAPE)
└── Continuity (value after the first study)
    ├── Daily job success ≥ 95%
    ├── Anomaly recall on injected spikes ≥ 90% (medium)
    └── False alarms ≤ 1 per user per week (replayed history)
```

## 2. Evaluation assets
| Asset | Content | Owner milestone |
|---|---|---|
| `eval/golden_questions.yaml` | 30–50 KO/EN questions spread across factual lookups (≈30%), comparisons/why (≈20%), dashboard commands (≈15%), regulation (≈20%), out-of-scope/no-evidence (≈15%). Each has expected tools, expected numbers (from data) and acceptable sources | M2–M4 |
| `eval/run_eval.py` | Runs the golden set against the agent; computes tool-selection accuracy, numeric faithfulness, citation precision, refusal accuracy; writes `eval/reports/agent_eval.md` | M4 |
| RAG query set | ~40 labeled queries → relevant document IDs; hit@k and MRR | M4 |
| Forecast backtest | Rolling-origin (train ≤ t, test t+1…t+3) per country × category; MAPE/RMSE vs naïve; model selection report | M2 |
| Anomaly tests | Inject synthetic spikes and drops (±20–60%) into history; measure recall/precision per signal; replay past periods to count alerts | M5 |
| Fuzz tests | Malformed tool/`ui_actions` JSON (truncated, missing keys, wrong types) → must repair, rewrite or drop without crashing | M4 |
| `eval/time_savings.py` | Scripted Playwright run: open → preset → category → 2 agent questions → report → export; N ≥ 10; median and p90 | M6 |
| Data validation | Pipeline output vs [03](03_data_analysis.md) reference numbers (±1%); coverage report | M1 |

## 3. Definitions
- **Numeric faithfulness:** share of numbers in agent answers that exactly match (after unit or rounding normalisation) a value in that turn's tool outputs.
- **Citation precision:** share of citations whose source actually supports the sentence they're attached to (automated check by source ID + manual audit on a sample).
- **Refusal accuracy:** share of no-evidence/out-of-scope questions answered with "no evidence" or a polite refusal instead of an invented answer.
- **P(TOP3):** share of weight draws (±20% perturbation; also reported for random Dirichlet weights) in which a country ranks in the TOP3.

## 4. Reporting
All evaluation results are written to `eval/reports/*.md`, linked from the README and summarised in the proposal. Every number cited in the proposal comes from these reports.
