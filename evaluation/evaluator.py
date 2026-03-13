import time

from evaluation.metrics import accuracy, completeness, exact_match
from normalization.hybrid_pipeline import hybrid_pipeline
from normalization.llm_pipeline import llm_pipeline
from normalization.rule_based_pipeline import rule_pipeline


def evaluate_pipeline(pipeline, dataset):
    acc_scores = []
    comp_scores = []
    exact_scores = []
    latency = []
    failures = 0

    for sample in dataset:
        raw = sample["input"]
        truth = sample["ground_truth"]

        start = time.perf_counter()
        try:
            pred = pipeline(raw)
        except Exception:
            pred = {}
            failures += 1
        latency.append(time.perf_counter() - start)

        acc_scores.append(accuracy(pred, truth))
        comp_scores.append(completeness(pred, truth))
        exact_scores.append(exact_match(pred, truth))

    total = len(dataset) or 1
    return {
        "accuracy": sum(acc_scores) / total,
        "completeness": sum(comp_scores) / total,
        "exact_match": sum(exact_scores) / total,
        "latency": sum(latency) / total,
        "failure_rate": failures / total,
    }


def run_evaluation(dataset):
    return {
        "rule": evaluate_pipeline(rule_pipeline, dataset),
        "llm": evaluate_pipeline(llm_pipeline, dataset),
        "hybrid": evaluate_pipeline(hybrid_pipeline, dataset),
    }
