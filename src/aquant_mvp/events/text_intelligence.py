from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re

import pandas as pd


@dataclass(frozen=True)
class TextIntelligenceCapability:
    capability_id: str
    layer: str
    role: str
    package_modules: tuple[str, ...]
    package_hint: str
    model_hint: str
    integration_status: str
    fallback_policy: str
    domestic_install_hint: str
    notes: str


@dataclass(frozen=True)
class SimilarEventResult:
    matches: pd.DataFrame
    summary: dict[str, object]
    markdown: str


SIMILAR_EVENT_COLUMNS = [
    "query_event_id",
    "query_published_at",
    "query_symbol",
    "query_event_type",
    "query_sentiment",
    "query_title",
    "match_event_id",
    "match_published_at",
    "match_symbol",
    "match_event_type",
    "match_sentiment",
    "match_title",
    "match_source",
    "match_source_url",
    "similarity_score",
    "same_symbol",
    "same_event_type",
    "pit_ok",
    "evidence_scope",
]


TEXT_INTELLIGENCE_REGISTRY: tuple[TextIntelligenceCapability, ...] = (
    TextIntelligenceCapability(
        "tfidf_similar_event_retrieval",
        "retrieval_explanation",
        "Native PIT-safe similar-event retrieval for stock news evidence reports",
        (),
        "stdlib+pandas+optional-scikit-learn",
        "local TF-IDF char n-gram cosine with deterministic Jaccard fallback",
        "native_supported",
        "fallback_to_jaccard_char_ngrams",
        "no install required; optional sklearn is already part of the modeling stack when available",
        "Writes similar_events and stock_similar_events reports. It is explanation evidence only and cannot promote trusted forecasts.",
    ),
    TextIntelligenceCapability(
        "sentence_transformers_bge_m3",
        "embedding",
        "Chinese financial/news embedding for semantic retrieval and similar-event search",
        ("sentence_transformers",),
        "sentence-transformers",
        "BAAI/bge-m3 or a locally mirrored Chinese embedding model",
        "candidate_optional",
        "fallback_to_rule_features_no_embedding",
        "pip install sentence-transformers -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Used only for retrieval/explanation when installed and locally available; never creates direct buy/sell signals.",
    ),
    TextIntelligenceCapability(
        "transformers_finbert_roberta",
        "event_classifier",
        "Supervised Chinese/financial transformer classifier for event type and sentiment",
        ("transformers",),
        "transformers",
        "FinBERT / Chinese RoBERTa / locally fine-tuned classifier",
        "candidate_optional",
        "fallback_to_audited_rule_classifier",
        "pip install transformers -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Current production path remains the rule classifier until a PIT-labeled event set proves value out of sample.",
    ),
    TextIntelligenceCapability(
        "torch_text_runtime",
        "model_runtime",
        "Local runtime for transformer/TabNet/TFT/graph text-event models",
        ("torch",),
        "torch",
        "Local CPU/GPU PyTorch runtime",
        "candidate_optional",
        "fallback_to_tabular_event_factors",
        "pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Deep text models are optional and must pass walk-forward evidence before affecting trusted status.",
    ),
    TextIntelligenceCapability(
        "faiss_vector_store",
        "vector_store",
        "Local vector index for similar news/event retrieval",
        ("faiss",),
        "faiss-cpu",
        "FAISS local index",
        "candidate_optional",
        "fallback_to_csv_duckdb_event_search",
        "pip install faiss-cpu -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Vector retrieval is for evidence and similar-history explanation, not direct order generation.",
    ),
    TextIntelligenceCapability(
        "lancedb_vector_store",
        "vector_store",
        "Local persistent vector database for event evidence",
        ("lancedb",),
        "lancedb",
        "LanceDB local table",
        "candidate_optional",
        "fallback_to_csv_duckdb_event_search",
        "pip install lancedb -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "Optional alternative to FAISS when persistent vector search is needed.",
    ),
    TextIntelligenceCapability(
        "qwen_local_summary",
        "summarization_extraction",
        "Local Qwen-family model for announcement/news summary and structured extraction",
        ("transformers",),
        "transformers",
        "Qwen local model path via AQUANT_QWEN_MODEL_PATH",
        "candidate_optional_requires_local_model",
        "fallback_to_source_snippet_and_rule_fields",
        "Set AQUANT_QWEN_MODEL_PATH to a local authorized model directory",
        "Summaries/extractions are evidence aids only; they never produce direct trading instructions.",
    ),
    TextIntelligenceCapability(
        "deepseek_local_summary",
        "summarization_extraction",
        "Local DeepSeek-family model for announcement/news summary and structured extraction",
        ("transformers",),
        "transformers",
        "DeepSeek local model path via AQUANT_DEEPSEEK_MODEL_PATH",
        "candidate_optional_requires_local_model",
        "fallback_to_source_snippet_and_rule_fields",
        "Set AQUANT_DEEPSEEK_MODEL_PATH to a local authorized model directory",
        "Summaries/extractions are evidence aids only; they never produce direct trading instructions.",
    ),
)


def build_similar_event_report(
    event_store: pd.DataFrame,
    *,
    bars_by_symbol: dict[str, pd.DataFrame] | None = None,
    symbol: str | None = None,
    horizons: tuple[int, ...] = (1, 5, 20),
    top_k: int = 5,
    query_events: int = 5,
    min_similarity: float = 0.05,
) -> SimilarEventResult:
    """Find PIT-safe similar historical events for explanation evidence.

    Retrieval is deliberately conservative: each query event can only match events
    published before it, and forward returns are reported only when the full
    return window ended before the query timestamp.
    """
    frame = _prepare_event_frame(event_store)
    columns = [*SIMILAR_EVENT_COLUMNS, *[f"forward_return_{h}d" for h in horizons], *[f"return_available_{h}d" for h in horizons]]
    if frame.empty:
        summary = _similar_event_summary(pd.DataFrame(columns=columns), horizons, query_count=0, symbol=symbol)
        return SimilarEventResult(pd.DataFrame(columns=columns), summary, _similar_event_markdown(pd.DataFrame(columns=columns), summary, horizons))

    if symbol:
        wanted = str(symbol).zfill(6)
        query_frame = frame[frame["symbol"].astype(str).str.zfill(6) == wanted].copy()
    else:
        query_frame = frame.copy()
    if query_frame.empty:
        summary = _similar_event_summary(pd.DataFrame(columns=columns), horizons, query_count=0, symbol=symbol)
        return SimilarEventResult(pd.DataFrame(columns=columns), summary, _similar_event_markdown(pd.DataFrame(columns=columns), summary, horizons))

    query_frame = (
        query_frame.sort_values("published_at")
        .groupby("symbol", group_keys=False)
        .tail(max(1, int(query_events)))
        .sort_values("published_at", ascending=False)
    )
    rows: list[dict[str, object]] = []
    for query in query_frame.itertuples(index=False):
        query_time = pd.Timestamp(query.published_at)
        candidates = frame[
            (frame["published_at"] < query_time)
            & (frame["event_id"].astype(str) != str(query.event_id))
            & (frame["text_for_similarity"].astype(str).str.len() > 0)
        ].copy()
        if candidates.empty:
            continue
        scores = _similarity_scores(str(query.text_for_similarity), candidates["text_for_similarity"].astype(str).tolist())
        candidates = candidates.assign(similarity_score=scores)
        candidates = candidates[candidates["similarity_score"] >= float(min_similarity)]
        if candidates.empty:
            continue
        candidates["same_symbol"] = candidates["symbol"].astype(str).str.zfill(6) == str(query.symbol).zfill(6)
        candidates["same_event_type"] = candidates["event_type"].astype(str) == str(query.event_type)
        candidates = candidates.sort_values(
            ["same_symbol", "same_event_type", "similarity_score", "published_at"],
            ascending=[False, False, False, False],
        ).head(max(1, int(top_k)))
        for match in candidates.itertuples(index=False):
            item = {
                "query_event_id": str(query.event_id),
                "query_published_at": query_time.isoformat(),
                "query_symbol": str(query.symbol).zfill(6),
                "query_event_type": str(query.event_type),
                "query_sentiment": str(query.sentiment),
                "query_title": str(query.title)[:240],
                "match_event_id": str(match.event_id),
                "match_published_at": pd.Timestamp(match.published_at).isoformat(),
                "match_symbol": str(match.symbol).zfill(6),
                "match_event_type": str(match.event_type),
                "match_sentiment": str(match.sentiment),
                "match_title": str(match.title)[:240],
                "match_source": str(match.source),
                "match_source_url": str(match.source_url),
                "similarity_score": float(match.similarity_score),
                "same_symbol": bool(match.same_symbol),
                "same_event_type": bool(match.same_event_type),
                "pit_ok": True,
                "evidence_scope": "past_events_only;returns_only_if_known_before_query",
            }
            item.update(_known_forward_returns(match, query_time, bars_by_symbol or {}, horizons))
            rows.append(item)
    matches = pd.DataFrame(rows, columns=columns)
    summary = _similar_event_summary(matches, horizons, query_count=int(len(query_frame)), symbol=symbol)
    return SimilarEventResult(matches, summary, _similar_event_markdown(matches, summary, horizons))


def discover_text_intelligence() -> pd.DataFrame:
    rows = []
    for item in TEXT_INTELLIGENCE_REGISTRY:
        installed_modules = [module for module in item.package_modules if importlib.util.find_spec(module) is not None]
        missing_modules = [module for module in item.package_modules if module not in installed_modules]
        local_model_ready = _local_model_ready(item.capability_id)
        installed = not missing_modules and local_model_ready
        version = _module_versions(installed_modules)
        rows.append(
            {
                **asdict(item),
                "package_modules": ",".join(item.package_modules),
                "installed": bool(installed),
                "installed_modules": ",".join(installed_modules),
                "missing_modules": ",".join(missing_modules),
                "local_model_ready": bool(local_model_ready),
                "version": version,
                "can_enter_event_factors": False,
                "decision_rule": "text models are evidence/retrieval aids until PIT labels and walk-forward gates prove value",
            }
        )
    return pd.DataFrame(rows).sort_values(["layer", "capability_id"]).reset_index(drop=True)


def write_text_intelligence_report(output_dir: Path, frame: pd.DataFrame | None = None) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = frame if frame is not None else discover_text_intelligence()
    paths = {
        "csv": output_dir / "text_intelligence_registry.csv",
        "md": output_dir / "text_intelligence_registry.md",
    }
    data.to_csv(paths["csv"], index=False)
    lines = [
        "# Text Intelligence Registry",
        "",
        "This registry records optional news/text intelligence bases for embeddings, event classification, summarization, and vector retrieval.",
        "",
        "These capabilities are evidence aids only. They do not issue trading instructions and cannot promote a signal to `trusted` without PIT labels, walk-forward evidence, and baseline comparison.",
        "",
        f"- total: {len(data)}",
        f"- installed_and_ready: {int(data['installed'].sum()) if not data.empty else 0}",
        "",
        "| capability | layer | installed | version | model_hint | fallback |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in data.itertuples(index=False):
        lines.append(
            f"| {row.capability_id} | {row.layer} | {row.installed} | {row.version} | {row.model_hint} | {row.fallback_policy} |"
        )
    paths["md"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths


def write_similar_event_outputs(output_dir: Path, result: SimilarEventResult, *, prefix: str = "similar_events") -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "csv": output_dir / f"{prefix}.csv",
        "json": output_dir / f"{prefix}.json",
        "md": output_dir / f"{prefix}.md",
    }
    result.matches.to_csv(paths["csv"], index=False)
    paths["json"].write_text(json.dumps(result.summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    paths["md"].write_text(result.markdown, encoding="utf-8")
    return paths


def _local_model_ready(capability_id: str) -> bool:
    if capability_id == "qwen_local_summary":
        return bool(os.getenv("AQUANT_QWEN_MODEL_PATH", "").strip())
    if capability_id == "deepseek_local_summary":
        return bool(os.getenv("AQUANT_DEEPSEEK_MODEL_PATH", "").strip())
    return True


def _module_versions(modules: list[str]) -> str:
    versions = []
    for module in modules:
        try:
            dist = {"sentence_transformers": "sentence-transformers", "faiss": "faiss-cpu"}.get(module, module)
            versions.append(f"{module}:{importlib.metadata.version(dist)}")
        except importlib.metadata.PackageNotFoundError:
            versions.append(f"{module}:unknown")
    return ",".join(versions)


def _prepare_event_frame(event_store: pd.DataFrame) -> pd.DataFrame:
    if event_store is None or event_store.empty:
        return pd.DataFrame()
    required = {"published_at", "symbol", "title"}
    if not required.issubset(event_store.columns):
        return pd.DataFrame()
    frame = event_store.copy()
    frame["published_at"] = pd.to_datetime(frame["published_at"], errors="coerce")
    frame["symbol"] = frame["symbol"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    frame = frame.dropna(subset=["published_at"])
    frame = frame[frame["symbol"].str.fullmatch(r"\d{6}", na=False)]
    if frame.empty:
        return pd.DataFrame()
    for column in ["event_id", "event_type", "sentiment", "summary", "source", "source_url", "entity_link_keywords", "source_category"]:
        if column not in frame.columns:
            frame[column] = ""
    frame["event_id"] = frame["event_id"].astype(str)
    missing_id = frame["event_id"].str.len() == 0
    frame.loc[missing_id, "event_id"] = frame.index[missing_id].map(lambda value: f"event_{value}")
    frame["text_for_similarity"] = frame.apply(_event_similarity_text, axis=1)
    return frame[frame["text_for_similarity"].str.len() > 0].reset_index(drop=True)


def _event_similarity_text(row: pd.Series) -> str:
    parts = [
        row.get("event_type", ""),
        row.get("sentiment", ""),
        row.get("title", ""),
        row.get("summary", ""),
        row.get("entity_link_keywords", ""),
        row.get("source_category", ""),
    ]
    return _normalize_text(" ".join(str(part) for part in parts if str(part).strip()))


def _normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value)).strip().lower()
    return value[:1200]


def _similarity_scores(query_text: str, candidate_texts: list[str]) -> list[float]:
    if not candidate_texts:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
        matrix = vectorizer.fit_transform([query_text, *candidate_texts])
        scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        return [float(score) for score in scores]
    except Exception:  # noqa: BLE001
        query_grams = _char_grams(query_text)
        scores = []
        for text in candidate_texts:
            grams = _char_grams(text)
            if not query_grams or not grams:
                scores.append(0.0)
                continue
            scores.append(float(len(query_grams & grams) / max(1, len(query_grams | grams))))
        return scores


def _char_grams(value: str) -> set[str]:
    clean = re.sub(r"\s+", "", value.lower())
    if len(clean) < 2:
        return {clean} if clean else set()
    grams: set[str] = set()
    for width in (2, 3, 4):
        if len(clean) >= width:
            grams.update(clean[idx : idx + width] for idx in range(0, len(clean) - width + 1))
    return grams


def _known_forward_returns(
    match: object,
    query_time: pd.Timestamp,
    bars_by_symbol: dict[str, pd.DataFrame],
    horizons: tuple[int, ...],
) -> dict[str, object]:
    out: dict[str, object] = {}
    match_symbol = str(getattr(match, "symbol", "")).zfill(6)
    bars = bars_by_symbol.get(match_symbol)
    for horizon in horizons:
        out[f"forward_return_{horizon}d"] = float("nan")
        out[f"return_available_{horizon}d"] = False
    if bars is None or bars.empty or "date" not in bars.columns or "close" not in bars.columns:
        return out
    frame = bars[["date", "close"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    if frame.empty:
        return out
    event_date = pd.Timestamp(getattr(match, "published_at")).normalize()
    query_date = query_time.normalize()
    entry_positions = frame.index[frame["date"] >= event_date].tolist()
    if not entry_positions:
        return out
    entry_pos = int(entry_positions[0])
    entry_close = float(frame.loc[entry_pos, "close"])
    if entry_close <= 0:
        return out
    for horizon in horizons:
        exit_pos = entry_pos + int(horizon)
        if exit_pos >= len(frame):
            continue
        exit_date = pd.Timestamp(frame.loc[exit_pos, "date"]).normalize()
        if exit_date >= query_date:
            continue
        exit_close = float(frame.loc[exit_pos, "close"])
        out[f"forward_return_{horizon}d"] = float(exit_close / entry_close - 1.0)
        out[f"return_available_{horizon}d"] = True
    return out


def _similar_event_summary(matches: pd.DataFrame, horizons: tuple[int, ...], query_count: int, symbol: str | None) -> dict[str, object]:
    summary: dict[str, object] = {
        "symbol": str(symbol).zfill(6) if symbol else "",
        "query_events": int(query_count),
        "match_rows": int(len(matches)),
        "pit_policy": "candidate events must be earlier than query events; forward returns require the return window to end before query time",
        "retrieval_model": "tfidf_char_cosine_with_jaccard_fallback",
        "can_enter_event_factors": False,
        "note": "Similar event retrieval is explanatory evidence only, not trading advice.",
    }
    for horizon in horizons:
        return_col = f"forward_return_{horizon}d"
        available_col = f"return_available_{horizon}d"
        if matches.empty or return_col not in matches.columns:
            summary[f"known_return_rows_{horizon}d"] = 0
            summary[f"mean_forward_return_{horizon}d"] = 0.0
            summary[f"positive_rate_{horizon}d"] = 0.0
            continue
        available = matches[matches[available_col].astype(bool)] if available_col in matches.columns else matches.iloc[0:0]
        returns = pd.to_numeric(available[return_col], errors="coerce").dropna()
        summary[f"known_return_rows_{horizon}d"] = int(len(returns))
        summary[f"mean_forward_return_{horizon}d"] = float(returns.mean()) if not returns.empty else 0.0
        summary[f"positive_rate_{horizon}d"] = float((returns > 0).mean()) if not returns.empty else 0.0
    if not matches.empty:
        summary["avg_similarity_score"] = float(pd.to_numeric(matches["similarity_score"], errors="coerce").mean())
        summary["same_symbol_rows"] = int(matches["same_symbol"].astype(bool).sum())
        summary["same_event_type_rows"] = int(matches["same_event_type"].astype(bool).sum())
    else:
        summary["avg_similarity_score"] = 0.0
        summary["same_symbol_rows"] = 0
        summary["same_event_type_rows"] = 0
    return summary


def _similar_event_markdown(matches: pd.DataFrame, summary: dict[str, object], horizons: tuple[int, ...]) -> str:
    lines = [
        "# Similar Event Evidence Report",
        "",
        "This report retrieves earlier structured events that resemble recent query events. It is an explanation layer only: it does not issue buy/sell advice and cannot promote a forecast to `trusted` without walk-forward evidence.",
        "",
        "## Summary",
        "",
        f"- Symbol: `{summary.get('symbol', '') or 'all'}`",
        f"- Query events: `{summary.get('query_events', 0)}`",
        f"- Matches: `{summary.get('match_rows', 0)}`",
        f"- Retrieval model: `{summary.get('retrieval_model', '')}`",
        f"- PIT policy: {summary.get('pit_policy', '')}",
        "",
        "## Historical Outcomes",
        "",
    ]
    for horizon in horizons:
        lines.append(
            f"- {horizon}d known rows: `{summary.get(f'known_return_rows_{horizon}d', 0)}`, "
            f"mean={float(summary.get(f'mean_forward_return_{horizon}d', 0.0)):.4%}, "
            f"positive_rate={float(summary.get(f'positive_rate_{horizon}d', 0.0)):.2%}"
        )
    lines.extend(["", "## Top Matches", ""])
    if matches.empty:
        lines.append("- No PIT-safe similar events were found.")
    else:
        for row in matches.head(30).itertuples(index=False):
            returns = []
            for horizon in horizons:
                available = bool(getattr(row, f"return_available_{horizon}d", False))
                value = getattr(row, f"forward_return_{horizon}d", float("nan"))
                returns.append(f"{horizon}d={'NA' if not available or pd.isna(value) else f'{float(value):.2%}'}")
            lines.append(
                f"- Query `{row.query_symbol}` {row.query_published_at} {row.query_event_type}: "
                f"matched `{row.match_symbol}` {row.match_published_at} {row.match_event_type} "
                f"score={float(row.similarity_score):.3f}, same_symbol={bool(row.same_symbol)}, "
                f"returns=({', '.join(returns)}); {row.match_title}"
            )
    lines.extend(["", "## Guardrails", "", "- Matches are restricted to events published before the query event.", "- Forward returns are omitted when they would not have been known at query time.", "- Retrieval evidence is not a trading signal."])
    return "\n".join(lines) + "\n"
