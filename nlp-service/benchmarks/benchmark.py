"""Day-5 benchmarks for the NLP service (Member 4).

1. Semantic search latency over N queries (target < 200 ms)
2. Sentiment accuracy of VADER on 100 reviews vs star-rating ground truth
   (and optionally DistilBERT-SST2 on the same sample, --distilbert)
3. Chatbot intent accuracy on the labelled query set from the tests
4. Search relevance: does the expected product appear in the top 3?

Usage (from nlp-service/, backend running or data/ exports present):
    python -m benchmarks.benchmark [--distilbert]
Writes reports/benchmark_results.json and reports/benchmark_results.md
"""

import argparse
import json
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_DIR))

from common.services import NLPServices  # noqa: E402
from sentiment.analyzer import SentimentAnalyzer, label_from_rating  # noqa: E402
from tests.test_intents import LABELLED_QUERIES  # noqa: E402

REPORT_DIR = SERVICE_DIR / "reports"

# (natural-language query, expected): expected is a product id that should be
# in the top 3, or a category name when several products are equally right
# answers (e.g. any headphones for "listen to music").
RELEVANCE_QUERIES = [
    ("something to keep my tea hot during lectures", 14),
    ("boil water for instant noodles in the hostel", 13),
    ("listen to music on the bus", "Audio"),
    ("quiet clicking mouse for the library", 10),
    ("carry my laptop and books to college in the rain", 15),
    ("charge my phone during a power cut", 12),
    ("solve matrices and complex numbers in the engineering exam", 11),
    ("light to read textbooks at night", 17),
    ("print my project report at home", 20),
    ("take handwritten notes on lecture slides with a pen", 5),
    ("move presentation files between computers", 19),
    ("hold my phone upright for video calls", 21),
    ("plug in all my chargers at the study desk", 18),
    ("budget laptop for programming", 3),
    ("type long assignments on a full size keyboard", 9),
]


def bench_search(services, runs=3):
    queries = [q for q, _ in RELEVANCE_QUERIES] + [
        "wireless earbuds", "gaming laptop", "cheap tablet", "5g phone", "backpack"]
    services.index.search("warm up", top_k=5)
    timings = []
    for _ in range(runs):
        for q in queries:
            start = time.perf_counter()
            services.index.search(q, top_k=10)
            timings.append((time.perf_counter() - start) * 1000)
    timings.sort()
    p95 = timings[int(len(timings) * 0.95) - 1]
    return {
        "queries": len(timings),
        "mean_ms": round(statistics.mean(timings), 2),
        "p50_ms": round(timings[len(timings) // 2], 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(timings[-1], 2),
        "target_ms": 200,
        "meets_target": p95 < 200,
    }


def bench_relevance(services):
    hits, rows = 0, []
    for query, expected in RELEVANCE_QUERIES:
        top = [h["product_id"] for h in services.index.search(query, top_k=3)]
        if isinstance(expected, str):
            ok = any(services.product(pid).get("category") == expected for pid in top)
        else:
            ok = expected in top
        hits += ok
        rows.append({"query": query, "expected": expected, "top3": top, "hit": ok})
    return {"hit_rate_at_3": round(hits / len(RELEVANCE_QUERIES), 3), "details": rows}


def _accuracy(pairs):
    correct = sum(p == t for p, t in pairs)
    per_class = {}
    for label in ("positive", "neutral", "negative"):
        subset = [(p, t) for p, t in pairs if t == label]
        if subset:
            per_class[label] = {"n": len(subset),
                                "accuracy": round(sum(p == t for p, t in subset) / len(subset), 3)}
    binary = [(p, t) for p, t in pairs if t != "neutral"]
    return {
        "accuracy_3class": round(correct / len(pairs), 3),
        "accuracy_pos_vs_neg": round(sum(p == t for p, t in binary) / len(binary), 3)
        if binary else None,
        "per_class": per_class,
        "confusion": {f"{t}->{p}": n for (p, t), n in Counter(pairs).items()},
    }


def bench_sentiment(services, sample_size=100, distilbert=False):
    reviews = [r for r in services.data.get_all_reviews() if r.get("comment")]
    rng = random.Random(7)
    sample = rng.sample(reviews, min(sample_size, len(reviews)))
    truth = [label_from_rating(r["rating"]) for r in sample]

    result = {
        "sample_size": len(sample),
        "ground_truth": "stars 4-5 positive, 3 neutral, 1-2 negative",
    }
    for key, analyzer in (("vader", SentimentAnalyzer(domain_lexicon=False)),
                          ("vader+domain", SentimentAnalyzer(domain_lexicon=True))):
        start = time.perf_counter()
        labels = [analyzer.label(r["comment"]) for r in sample]
        elapsed = (time.perf_counter() - start) * 1000
        result[key] = {**_accuracy(list(zip(labels, truth))),
                       "ms_per_review": round(elapsed / len(sample), 3)}

    if distilbert:
        try:
            from transformers import pipeline
            clf = pipeline("sentiment-analysis",
                           model="distilbert-base-uncased-finetuned-sst-2-english",
                           device=-1)
            start = time.perf_counter()
            outputs = clf([r["comment"] for r in sample], truncation=True, batch_size=16)
            bert_ms = (time.perf_counter() - start) * 1000
            # SST-2 is binary; treat low-confidence predictions as neutral.
            bert = ["neutral" if o["score"] < 0.75 else o["label"].lower() for o in outputs]
            result["distilbert"] = {**_accuracy(list(zip(bert, truth))),
                                    "ms_per_review": round(bert_ms / len(sample), 3)}
        except Exception as error:  # noqa: BLE001
            result["distilbert"] = {"error": str(error)}
    return result


def bench_intents(services):
    rows = []
    for message, expected in LABELLED_QUERIES:
        predicted = services.classifier.classify(message).name
        rows.append({"message": message, "expected": expected, "predicted": predicted})
    correct = sum(r["expected"] == r["predicted"] for r in rows)
    return {"queries": len(rows), "accuracy": round(correct / len(rows), 3),
            "errors": [r for r in rows if r["expected"] != r["predicted"]]}


def to_markdown(results):
    s, sent, rel, intents = (results["search_latency"], results["sentiment"],
                             results["search_relevance"], results["intents"])
    lines = [
        "# NLP service benchmark results", "",
        f"Embedding engine: `{results['engine']}` · data source: `{results['data_source']}`", "",
        "## Semantic search latency",
        f"- {s['queries']} queries · mean **{s['mean_ms']} ms** · p50 {s['p50_ms']} ms · "
        f"p95 **{s['p95_ms']} ms** · max {s['max_ms']} ms",
        f"- Target < 200 ms: **{'met' if s['meets_target'] else 'NOT met'}**", "",
        "## Search relevance (expected product in top 3)",
        f"- Hit rate@3: **{rel['hit_rate_at_3'] * 100:.0f}%** on {len(rel['details'])} "
        "natural-language queries", "",
        "| Query | Expected | Top 3 | Hit |", "|---|---|---|---|",
    ]
    lines += [f"| {d['query']} | {d['expected']} | {d['top3']} | {'yes' if d['hit'] else 'NO'} |"
              for d in rel["details"]]
    lines += ["", f"## Sentiment vs star ratings ({sent['sample_size']} reviews)",
              f"Ground truth: {sent['ground_truth']}", "",
              "| Model | 3-class accuracy | Positive vs negative | ms / review |",
              "|---|---|---|---|"]
    for name in ("vader", "vader+domain", "distilbert"):
        if name in sent and "error" not in sent[name]:
            m = sent[name]
            lines.append(f"| {name} | {m['accuracy_3class'] * 100:.0f}% | "
                         f"{m['accuracy_pos_vs_neg'] * 100:.0f}% | {m['ms_per_review']} |")
        elif name in sent:
            lines.append(f"| {name} | error: {sent[name]['error']} | | |")
    lines += ["", "Per-class (VADER + domain lexicon, used in production): " + ", ".join(
        f"{k} {v['accuracy'] * 100:.0f}% (n={v['n']})"
        for k, v in sent["vader+domain"]["per_class"].items()),
        "", "Note: the review corpus is synthetic demo data (see backend/scripts/review_bank.py). "
        "3-star reviews are deliberately mixed, so the neutral class is the hardest.", "",
        "## Chatbot intent classification",
        f"- {intents['queries']} labelled queries · accuracy **{intents['accuracy'] * 100:.0f}%**"]
    for e in intents["errors"]:
        lines.append(f"  - \"{e['message']}\": expected {e['expected']}, got {e['predicted']}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--distilbert", action="store_true",
                        help="also evaluate DistilBERT-SST2 (downloads ~250MB once)")
    args = parser.parse_args()

    services = NLPServices()
    services.sync()
    results = {
        "engine": services.index.engine,
        "data_source": services.data.last_source,
        "search_latency": bench_search(services),
        "search_relevance": bench_relevance(services),
        "sentiment": bench_sentiment(services, distilbert=args.distilbert),
        "intents": bench_intents(services),
    }
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "benchmark_results.json").write_text(json.dumps(results, indent=2),
                                                       encoding="utf-8")
    markdown = to_markdown(results)
    (REPORT_DIR / "benchmark_results.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
