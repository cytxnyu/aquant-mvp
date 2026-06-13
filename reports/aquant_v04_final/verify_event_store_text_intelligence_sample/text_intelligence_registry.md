# Text Intelligence Registry

This registry records optional news/text intelligence bases for embeddings, event classification, summarization, and vector retrieval.

These capabilities are evidence aids only. They do not issue trading instructions and cannot promote a signal to `trusted` without PIT labels, walk-forward evidence, and baseline comparison.

- total: 8
- installed_and_ready: 3

| capability | layer | installed | version | model_hint | fallback |
| --- | --- | ---: | --- | --- | --- |
| sentence_transformers_bge_m3 | embedding | False |  | BAAI/bge-m3 or a locally mirrored Chinese embedding model | fallback_to_rule_features_no_embedding |
| transformers_finbert_roberta | event_classifier | True | transformers:4.52.4 | FinBERT / Chinese RoBERTa / locally fine-tuned classifier | fallback_to_audited_rule_classifier |
| torch_text_runtime | model_runtime | True | torch:2.7.0 | Local CPU/GPU PyTorch runtime | fallback_to_tabular_event_factors |
| tfidf_similar_event_retrieval | retrieval_explanation | True |  | local TF-IDF char n-gram cosine with deterministic Jaccard fallback | fallback_to_jaccard_char_ngrams |
| deepseek_local_summary | summarization_extraction | False | transformers:4.52.4 | DeepSeek local model path via AQUANT_DEEPSEEK_MODEL_PATH | fallback_to_source_snippet_and_rule_fields |
| qwen_local_summary | summarization_extraction | False | transformers:4.52.4 | Qwen local model path via AQUANT_QWEN_MODEL_PATH | fallback_to_source_snippet_and_rule_fields |
| faiss_vector_store | vector_store | False |  | FAISS local index | fallback_to_csv_duckdb_event_search |
| lancedb_vector_store | vector_store | False |  | LanceDB local table | fallback_to_csv_duckdb_event_search |
