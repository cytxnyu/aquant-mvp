# Event Impact Study

This report tests how structured events behaved historically after publication. It is ex-post audit evidence and a PIT-prior diagnostic, not a trading instruction.

## Summary

- Event rows: `23522`
- Event-return rows: `70566`
- Available return rows: `64979`
- Cohort rows: `178`
- PIT-prior rows: `70566`
- PIT-ready rows: `68973`
- No future leakage: `True`
- Can enter trusted model directly: `False`

## Top Cohorts

- sentiment `neutral` h=1 n=17013, mean=-0.1453%, positive=45.65%, t=-5.57, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=1 n=16895, mean=-0.0936%, positive=46.42%, t=-3.59, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=5 n=16557, mean=0.5526%, positive=49.42%, t=9.42, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=5 n=16216, mean=0.3896%, positive=48.13%, t=6.58, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `official_disclosure` h=20 n=15300, mean=1.3563%, positive=48.97%, t=11.27, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `neutral` h=20 n=14539, mean=1.1351%, positive=48.35%, t=9.27, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `general_news` h=1 n=13907, mean=-0.1481%, positive=45.63%, t=-5.10, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `general_news|neutral` h=1 n=13906, mean=-0.1479%, positive=45.63%, t=-5.09, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `general_news` h=5 n=13451, mean=0.4944%, positive=49.03%, t=7.66, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `general_news|neutral` h=5 n=13450, mean=0.4950%, positive=49.03%, t=7.67, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `general_news|high` h=1 n=13235, mean=-0.1157%, positive=46.18%, t=-3.89, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `general_news|high` h=5 n=13002, mean=0.5812%, positive=49.73%, t=8.86, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `general_news` h=20 n=12422, mean=1.0694%, positive=48.24%, t=8.07, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `general_news|neutral` h=20 n=12422, mean=1.0694%, positive=48.24%, t=8.07, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `general_news|high` h=20 n=12254, mean=1.1593%, positive=48.55%, t=8.68, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=1 n=5005, mean=0.0531%, positive=48.51%, t=1.05, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=5 n=4821, mean=0.4544%, positive=48.41%, t=3.68, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `commodity_shock|medium` h=1 n=4670, mean=0.0209%, positive=47.77%, t=0.40, status=watchlist; sample_count=4670, t_stat=0.40
- source_category `market_data` h=1 n=4553, mean=0.0121%, positive=47.73%, t=0.23, status=watchlist; sample_count=4553, t_stat=0.23
- event_type_reliability `commodity_shock|medium` h=5 n=4499, mean=0.3521%, positive=47.83%, t=2.72, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `market_data` h=5 n=4432, mean=0.4086%, positive=48.15%, t=3.14, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type `commodity_shock` h=20 n=4415, mean=2.9465%, positive=54.41%, t=12.47, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_reliability `commodity_shock|medium` h=20 n=4125, mean=2.7334%, positive=53.87%, t=11.15, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- source_category `market_data` h=20 n=4112, mean=2.7665%, positive=53.99%, t=11.26, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- sentiment `positive` h=1 n=3665, mean=0.0407%, positive=46.96%, t=0.70, status=watchlist; sample_count=3665, t_stat=0.70
- sentiment `positive` h=5 n=3513, mean=-0.1069%, positive=45.06%, t=-0.74, status=watchlist; sample_count=3513, t_stat=-0.74
- sentiment `positive` h=20 n=3172, mean=1.2937%, positive=48.33%, t=4.59, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=1 n=2855, mean=0.0269%, positive=47.18%, t=0.39, status=watchlist; sample_count=2855, t_stat=0.39
- event_type_sentiment `commodity_shock|positive` h=5 n=2767, mean=-0.2572%, positive=44.31%, t=-1.53, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use
- event_type_sentiment `commodity_shock|positive` h=20 n=2590, mean=1.1397%, positive=48.46%, t=3.65, status=candidate_for_walk_forward; requires walk-forward baseline comparison before model use

## Guardrails

- Cohort statistics are ex-post validation evidence; they are not direct buy/sell signals.
- `pit_priors` only uses earlier events whose outcome window was already complete before the query event.
- `can_enter_trusted_model` remains false until large-universe walk-forward evidence proves event factors beat baselines.
