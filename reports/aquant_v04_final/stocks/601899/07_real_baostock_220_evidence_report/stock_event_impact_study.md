# Event Impact Study

This report tests how structured events behaved historically after publication. It is ex-post audit evidence and a PIT-prior diagnostic, not a trading instruction.

## Summary

- Event rows: `1500`
- Event-return rows: `6000`
- Available return rows: `4714`
- Cohort rows: `181`
- PIT-prior rows: `6000`
- PIT-ready rows: `4482`
- No future leakage: `True`
- Can enter trusted model directly: `False`

## Top Cohorts

- source_category `official_disclosure` h=1 n=1326, mean=0.3475%, positive=50.83%, t=3.65, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=5 n=1287, mean=1.1720%, positive=52.91%, t=5.21, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=20 n=1078, mean=4.0398%, positive=55.94%, t=8.04, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=1 n=797, mean=0.2163%, positive=49.31%, t=1.79, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=5 n=765, mean=0.4006%, positive=48.10%, t=1.40, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `shareholder_change` h=1 n=699, mean=0.0469%, positive=47.35%, t=0.37, status=watchlist; sample_count=699, t_stat=0.37
- event_type_reliability `shareholder_change|high` h=1 n=699, mean=0.0469%, positive=47.35%, t=0.37, status=watchlist; sample_count=699, t_stat=0.37
- event_type_sentiment `shareholder_change|neutral` h=1 n=699, mean=0.0469%, positive=47.35%, t=0.37, status=watchlist; sample_count=699, t_stat=0.37
- event_type `shareholder_change` h=5 n=673, mean=0.1948%, positive=45.62%, t=0.63, status=watchlist; sample_count=673, t_stat=0.63
- event_type_reliability `shareholder_change|high` h=5 n=673, mean=0.1948%, positive=45.62%, t=0.63, status=watchlist; sample_count=673, t_stat=0.63
- event_type_sentiment `shareholder_change|neutral` h=5 n=673, mean=0.1948%, positive=45.62%, t=0.63, status=watchlist; sample_count=673, t_stat=0.63
- sentiment `neutral` h=20 n=620, mean=2.0523%, positive=51.29%, t=3.26, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=1 n=574, mean=0.4444%, positive=53.83%, t=3.20, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=5 n=568, mean=1.8336%, positive=57.57%, t=5.67, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `shareholder_change` h=20 n=531, mean=1.8810%, positive=50.28%, t=2.70, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `shareholder_change|high` h=20 n=531, mean=1.8810%, positive=50.28%, t=2.70, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `shareholder_change|neutral` h=20 n=531, mean=1.8810%, positive=50.28%, t=2.70, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=20 n=511, mean=4.4704%, positive=57.53%, t=6.21, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=60 n=459, mean=5.3716%, positive=48.15%, t=4.41, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=1 n=388, mean=0.3867%, positive=57.22%, t=2.26, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=5 n=382, mean=1.5437%, positive=56.54%, t=4.65, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=20 n=357, mean=3.2257%, positive=57.70%, t=4.64, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=1 n=317, mean=0.4642%, positive=59.94%, t=2.50, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=5 n=315, mean=1.6692%, positive=56.19%, t=4.44, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=20 n=299, mean=3.6565%, positive=57.86%, t=4.56, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=60 n=256, mean=4.3898%, positive=48.05%, t=3.01, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=60 n=255, mean=3.6895%, positive=44.31%, t=2.17, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `shareholder_change` h=60 n=235, mean=4.3124%, positive=46.38%, t=2.37, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `shareholder_change|high` h=60 n=235, mean=4.3124%, positive=46.38%, t=2.37, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `shareholder_change|neutral` h=60 n=235, mean=4.3124%, positive=46.38%, t=2.37, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use

## Guardrails

- Cohort statistics are ex-post validation evidence; they are not direct buy/sell signals.
- `pit_priors` only uses earlier events whose outcome window was already complete before the query event.
- `can_enter_trusted_model` remains false until large-universe walk-forward evidence proves event factors beat baselines.
