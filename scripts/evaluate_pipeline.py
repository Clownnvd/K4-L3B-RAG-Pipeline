"""Run reproducible A/B evaluation on the checked-in golden dataset.

Config A uses dense-only retrieval.  Config B uses query planning, BM25,
dense retrieval, RRF and cross-knowledge-base coverage.  Both use the same
deterministic extractive generator so retrieval is the only changed variable.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.task10_generation import _extractive_fallback
from src.task4_chunking_indexing import embed_texts
from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task9_retrieval_pipeline import retrieve


EVAL_DIR = ROOT / "group_project" / "evaluation"
DATASET_PATH = EVAL_DIR / "golden_dataset.json"
OUTPUT_PATH = EVAL_DIR / "retrieval_results.json"
REPORT_PATH = EVAL_DIR / "RESULT.md"
TOP_K = 6


def source_id(result: dict) -> str:
    return result["id"].split("::", 1)[0]


def tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"\w+", text.casefold(), re.UNICODE) if len(token) >= 3}


def context_metrics(results: list[dict], expected_sources: list[str]) -> tuple[float, float]:
    retrieved = [source_id(result) for result in results]
    expected = set(expected_sources)
    found = expected & set(retrieved)
    recall = len(found) / len(expected) if expected else 1.0
    precision = sum(item in expected for item in retrieved) / len(retrieved) if retrieved else 0.0
    return recall, precision


def faithfulness_proxy(answer: str, results: list[dict]) -> float:
    contexts = [result["content"] for result in results]
    context_sets = [tokens(context) for context in contexts]
    claims = [
        line.lstrip("- ").strip()
        for line in answer.splitlines()
        if line.strip().startswith("-") and len(line.strip()) >= 30
    ]
    if not claims:
        return 0.0
    supported = 0
    for claim in claims:
        claim_tokens = tokens(re.sub(r"\[S\d+\]", "", claim))
        if not claim_tokens:
            continue
        overlap = max((len(claim_tokens & context) / len(claim_tokens) for context in context_sets), default=0.0)
        supported += overlap >= 0.80
    return supported / len(claims)


def run_config(case: dict, config: str) -> dict:
    started = time.perf_counter()
    if config == "A":
        results = semantic_search(case["question"], top_k=TOP_K)
    else:
        results = retrieve(case["question"], top_k=TOP_K)
    latency_ms = (time.perf_counter() - started) * 1000
    answer = _extractive_fallback(case["question"], results)
    recall, precision = context_metrics(results, case["expected_sources"])
    return {
        "results": results,
        "answer": answer,
        "context_recall": recall,
        "context_precision": precision,
        "faithfulness": faithfulness_proxy(answer, results),
        "latency_ms": latency_ms,
    }


def add_answer_relevance(records: list[dict], dataset: list[dict]) -> None:
    texts = []
    for record, case in zip(records, dataset):
        texts.extend([record["answer"], case["expected_answer"]])
    vectors = embed_texts(texts)
    for index, record in enumerate(records):
        answer_vector = np.asarray(vectors[index * 2], dtype=float)
        expected_vector = np.asarray(vectors[index * 2 + 1], dtype=float)
        record["answer_relevance"] = float(np.dot(answer_vector, expected_vector))


def average(records: list[dict], metric: str) -> float:
    return sum(record[metric] for record in records) / len(records)


def serializable(record: dict) -> dict:
    return {
        **{key: value for key, value in record.items() if key != "results"},
        "retrieved": [
            {
                "id": item["id"], "score": item["score"],
                "title": item["metadata"]["title"],
                "knowledge_base": item["metadata"].get("knowledge_base"),
            }
            for item in record["results"]
        ],
    }


def write_report(dataset: list[dict], configs: dict[str, list[dict]]) -> None:
    metrics = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]
    scores = {name: {metric: average(rows, metric) for metric in metrics} for name, rows in configs.items()}
    worst = sorted(
        range(len(dataset)),
        key=lambda i: sum(configs["B"][i][metric] for metric in metrics) / len(metrics),
    )[:3]
    lines = [
        "# RAG evaluation result",
        "",
        "## Reproducibility setup",
        "",
        "| Field | Value |",
        "|---|---|",
        "| Corpus | 3 legal documents + 8 news articles |",
        "| Golden dataset | 18 grounded cases |",
        "| Config A | Dense-only, top_k=6 |",
        "| Config B | Query planning + Dense + BM25 + RRF + News/Law coverage, top_k=6 |",
        "| Generator held constant | Deterministic extractive generator |",
        "| Embedding model | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |",
        "| Metric implementation | Reproducible local proxies; no external judge |",
        "",
        "## Overall scores",
        "",
        "| Metric | Config A | Config B | Delta B-A |",
        "|---|---:|---:|---:|",
    ]
    for metric in metrics:
        a, b = scores["A"][metric], scores["B"][metric]
        lines.append(f"| {metric} | {a:.3f} | {b:.3f} | {b-a:+.3f} |")
    latency_a = average(configs["A"], "latency_ms")
    latency_b = average(configs["B"], "latency_ms")
    lines.extend(
        [
            "",
            "## A/B comparison",
            "",
            f"Config B changes only retrieval strategy. Mean latency changed from {latency_a:.1f} ms to {latency_b:.1f} ms. "
            "The decision criterion is evidence coverage and noise, not average score alone.",
            "",
            "## Worst performers",
            "",
            "| Case | Question | Root cause |",
            "|---:|---|---|",
        ]
    )
    for index in worst:
        row = configs["B"][index]
        if row["context_recall"] < 1:
            cause = "Retrieval missed at least one expected source."
        elif row["context_precision"] < 0.34:
            cause = "Top-k contains extra sources; reranking/threshold needs tuning."
        else:
            cause = "Evidence is present; answer phrasing differs from the reference."
        lines.append(f"| {index+1} | {dataset[index]['question']} | {cause} |")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "1. Tune cross-KB quotas and BM25 normalization on the three worst cases, then rerun the same 18 cases.",
            "2. Add a cross-encoder reranker only if it improves context precision without reducing context recall.",
            "3. Calibrate the dense fallback threshold using in-domain and out-of-domain queries; do not use RRF score for fallback.",
            "4. Run a second evaluation with an LLM judge before final submission; keep this local run as the reproducible baseline.",
            "",
            "## Metric notes",
            "",
            "- Faithfulness: proportion of extractive claims whose content tokens are supported by retrieved chunks.",
            "- Answer relevance: cosine similarity between generated and expected answers using the fixed multilingual embedding model.",
            "- Context recall: proportion of expected source documents retrieved.",
            "- Context precision: proportion of retrieved chunks belonging to expected source documents.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    # Warm model, Chroma and BM25 before timing either configuration.
    semantic_search("khởi động đánh giá", top_k=1)
    lexical_search("khởi động đánh giá", top_k=1)
    configs = {"A": [], "B": []}
    for index, case in enumerate(dataset, 1):
        print(f"[{index:02d}/{len(dataset)}] {case['question']}")
        configs["A"].append(run_config(case, "A"))
        configs["B"].append(run_config(case, "B"))
    add_answer_relevance(configs["A"], dataset)
    add_answer_relevance(configs["B"], dataset)
    payload = {
        "config_a": [serializable(row) for row in configs["A"]],
        "config_b": [serializable(row) for row in configs["B"]],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(dataset, configs)
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
