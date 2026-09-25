# RAG evaluation result

## Reproducibility setup

| Field | Value |
|---|---|
| Corpus | 3 legal documents + 8 news articles |
| Golden dataset | 18 grounded cases |
| Config A | Dense-only, top_k=6 |
| Config B | Query planning + Dense + BM25 + RRF + News/Law coverage, top_k=6 |
| Generator held constant | Deterministic extractive generator |
| Embedding model | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| Metric implementation | Reproducible local proxies; no external judge |

## Overall scores

| Metric | Config A | Config B | Delta B-A |
|---|---:|---:|---:|
| faithfulness | 1.000 | 1.000 | +0.000 |
| answer_relevance | 0.474 | 0.493 | +0.018 |
| context_recall | 0.500 | 1.000 | +0.500 |
| context_precision | 0.343 | 0.630 | +0.287 |

## A/B comparison

Config B changes only retrieval strategy. Mean latency changed from 74.4 ms to 91.4 ms. The decision criterion is evidence coverage and noise, not average score alone.

## Worst performers

| Case | Question | Root cause |
|---:|---|---|
| 6 | Hành vi sử dụng trái phép chất ma túy bị xử phạt hành chính thế nào theo Nghị định 144/2021? | Top-k contains extra sources; reranking/threshold needs tuning. |
| 2 | Vụ việc liên quan Miu Lê được kiểm tra lúc nào và có bao nhiêu người liên quan? | Top-k contains extra sources; reranking/threshold needs tuning. |
| 14 | Đường dây xuyên biên giới trong corpus bị khởi tố về những nhóm hành vi ma túy nào? | Top-k contains extra sources; reranking/threshold needs tuning. |

## Recommendations

1. Tune cross-KB quotas and BM25 normalization on the three worst cases, then rerun the same 18 cases.
2. Add a cross-encoder reranker only if it improves context precision without reducing context recall.
3. Calibrate the dense fallback threshold using in-domain and out-of-domain queries; do not use RRF score for fallback.
4. Run a second evaluation with an LLM judge before final submission; keep this local run as the reproducible baseline.

## Metric notes

- Faithfulness: proportion of extractive claims whose content tokens are supported by retrieved chunks.
- Answer relevance: cosine similarity between generated and expected answers using the fixed multilingual embedding model.
- Context recall: proportion of expected source documents retrieved.
- Context precision: proportion of retrieved chunks belonging to expected source documents.
