# Event Impact Study

This report tests how structured events behaved historically after publication. It is ex-post audit evidence and a PIT-prior diagnostic, not a trading instruction.

## Summary

- Event rows: `12`
- Event-return rows: `36`
- Available return rows: `13`
- Cohort rows: `17`
- PIT-prior rows: `36`
- PIT-ready rows: `0`
- No future leakage: `True`
- Can enter trusted model directly: `False`

## Top Cohorts

- source_category `sample_demo` h=1 n=11, mean=0.6752%, positive=45.45%, t=0.74, status=data_insufficient; sample_count=11, minimum=20
- sentiment `positive` h=1 n=8, mean=0.3585%, positive=25.00%, t=0.29, status=data_insufficient; sample_count=8, minimum=20
- event_type `commodity_shock` h=1 n=6, mean=0.8543%, positive=33.33%, t=0.53, status=data_insufficient; sample_count=6, minimum=20
- event_type_reliability `commodity_shock|low` h=1 n=6, mean=0.8543%, positive=33.33%, t=0.53, status=data_insufficient; sample_count=6, minimum=20
- event_type_sentiment `commodity_shock|positive` h=1 n=6, mean=0.8543%, positive=33.33%, t=0.53, status=data_insufficient; sample_count=6, minimum=20
- event_type `public_opinion_risk` h=1 n=3, mean=1.5198%, positive=100.00%, t=1.97, status=data_insufficient; sample_count=3, minimum=20
- event_type_reliability `public_opinion_risk|low` h=1 n=3, mean=1.5198%, positive=100.00%, t=1.97, status=data_insufficient; sample_count=3, minimum=20
- event_type_sentiment `public_opinion_risk|negative` h=1 n=3, mean=1.5198%, positive=100.00%, t=1.97, status=data_insufficient; sample_count=3, minimum=20
- sentiment `negative` h=1 n=3, mean=1.5198%, positive=100.00%, t=1.97, status=data_insufficient; sample_count=3, minimum=20
- event_type `order_contract` h=1 n=2, mean=-1.1289%, positive=0.00%, t=-1.29, status=data_insufficient; sample_count=2, minimum=20
- event_type_reliability `order_contract|low` h=1 n=2, mean=-1.1289%, positive=0.00%, t=-1.29, status=data_insufficient; sample_count=2, minimum=20
- event_type_sentiment `order_contract|positive` h=1 n=2, mean=-1.1289%, positive=0.00%, t=-1.29, status=data_insufficient; sample_count=2, minimum=20
- event_type `public_opinion_risk` h=5 n=2, mean=6.8115%, positive=50.00%, t=0.85, status=data_insufficient; sample_count=2, minimum=20
- event_type_reliability `public_opinion_risk|low` h=5 n=2, mean=6.8115%, positive=50.00%, t=0.85, status=data_insufficient; sample_count=2, minimum=20
- event_type_sentiment `public_opinion_risk|negative` h=5 n=2, mean=6.8115%, positive=50.00%, t=0.85, status=data_insufficient; sample_count=2, minimum=20
- sentiment `negative` h=5 n=2, mean=6.8115%, positive=50.00%, t=0.85, status=data_insufficient; sample_count=2, minimum=20
- source_category `sample_demo` h=5 n=2, mean=6.8115%, positive=50.00%, t=0.85, status=data_insufficient; sample_count=2, minimum=20

## Guardrails

- Cohort statistics are ex-post validation evidence; they are not direct buy/sell signals.
- `pit_priors` only uses earlier events whose outcome window was already complete before the query event.
- `can_enter_trusted_model` remains false until large-universe walk-forward evidence proves event factors beat baselines.
