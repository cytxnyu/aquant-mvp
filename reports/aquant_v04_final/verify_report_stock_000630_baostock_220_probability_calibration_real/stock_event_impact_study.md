# Event Impact Study

This report tests how structured events behaved historically after publication. It is ex-post audit evidence and a PIT-prior diagnostic, not a trading instruction.

## Summary

- Event rows: `1500`
- Event-return rows: `6000`
- Available return rows: `4732`
- Cohort rows: `179`
- PIT-prior rows: `6000`
- PIT-ready rows: `4412`
- No future leakage: `True`
- Can enter trusted model directly: `False`

## Top Cohorts

- source_category `official_disclosure` h=1 n=1323, mean=0.1471%, positive=46.49%, t=1.56, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=5 n=1291, mean=1.0213%, positive=50.58%, t=4.47, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=20 n=1081, mean=3.9005%, positive=55.13%, t=7.75, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=1 n=799, mean=-0.0726%, positive=42.43%, t=-0.61, status=watchlist; sample_count=799, t_stat=-0.61
- sentiment `neutral` h=5 n=774, mean=0.2632%, positive=45.09%, t=0.91, status=watchlist; sample_count=774, t_stat=0.91
- event_type `shareholder_change` h=1 n=699, mean=-0.0238%, positive=45.49%, t=-0.19, status=watchlist; sample_count=699, t_stat=-0.19
- event_type_reliability `shareholder_change|high` h=1 n=699, mean=-0.0238%, positive=45.49%, t=-0.19, status=watchlist; sample_count=699, t_stat=-0.19
- event_type_sentiment `shareholder_change|neutral` h=1 n=699, mean=-0.0238%, positive=45.49%, t=-0.19, status=watchlist; sample_count=699, t_stat=-0.19
- event_type `shareholder_change` h=5 n=676, mean=0.2039%, positive=44.53%, t=0.64, status=watchlist; sample_count=676, t_stat=0.64
- event_type_reliability `shareholder_change|high` h=5 n=676, mean=0.2039%, positive=44.53%, t=0.64, status=watchlist; sample_count=676, t_stat=0.64
- event_type_sentiment `shareholder_change|neutral` h=5 n=676, mean=0.2039%, positive=44.53%, t=0.64, status=watchlist; sample_count=676, t_stat=0.64
- sentiment `neutral` h=20 n=628, mean=2.0530%, positive=50.48%, t=3.26, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=1 n=568, mean=0.3909%, positive=51.94%, t=2.63, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=5 n=562, mean=1.8586%, positive=58.54%, t=5.24, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `shareholder_change` h=20 n=537, mean=2.3845%, positive=51.02%, t=3.39, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `shareholder_change|high` h=20 n=537, mean=2.3845%, positive=51.02%, t=3.39, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `shareholder_change|neutral` h=20 n=537, mean=2.3845%, positive=51.02%, t=3.39, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=20 n=505, mean=5.4571%, positive=59.80%, t=7.21, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=60 n=466, mean=5.0803%, positive=50.43%, t=4.80, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=1 n=384, mean=0.3058%, positive=54.43%, t=1.62, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=5 n=379, mean=1.3749%, positive=56.99%, t=3.43, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=20 n=358, mean=4.5121%, positive=59.22%, t=5.78, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=1 n=313, mean=0.4316%, positive=56.87%, t=2.05, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=5 n=311, mean=1.7965%, positive=59.16%, t=3.95, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=20 n=295, mean=5.3506%, positive=61.69%, t=6.01, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=60 n=264, mean=3.2427%, positive=48.48%, t=2.48, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=60 n=257, mean=4.8326%, positive=51.36%, t=3.37, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `shareholder_change` h=60 n=234, mean=3.3927%, positive=46.58%, t=2.33, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `shareholder_change|high` h=60 n=234, mean=3.3927%, positive=46.58%, t=2.33, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `shareholder_change|neutral` h=60 n=234, mean=3.3927%, positive=46.58%, t=2.33, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use

## Guardrails

- Cohort statistics are ex-post validation evidence; they are not direct buy/sell signals.
- `pit_priors` only uses earlier events whose outcome window was already complete before the query event.
- `can_enter_trusted_model` remains false until large-universe walk-forward evidence proves event factors beat baselines.
