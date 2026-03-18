import os
import statistics
import time

from evaluation.metrics import accuracy, completeness, exact_match
from normalization.hybrid_pipeline import hybrid_pipeline
from normalization.llm_pipeline import clear_llm_cache, llm_pipeline
from normalization.rule_based_pipeline import rule_pipeline
from utils.llm_client import get_llm_model, snapshot_usage


PIPELINES = {
    "rule": rule_pipeline,
    "llm": llm_pipeline,
    "hybrid": hybrid_pipeline,
}


def _get_benchmark_runs():
    try:
        return max(1, int(os.getenv("BENCHMARK_RUNS", "1")))
    except ValueError:
        return 1


BENCHMARK_RUNS = _get_benchmark_runs()


def build_sample_callback(sample_callback, dataset_name, pipeline_name):
    if sample_callback is None:
        return None

    # Attach dataset/pipeline metadata once so the inner evaluation loop stays simple.
    def callback(index, total, record, current_predictions):
        sample_callback(
            dataset_name,
            pipeline_name,
            index,
            total,
            record,
            current_predictions,
        )

    return callback


def evaluate_pipeline(pipeline, dataset, sample_callback=None):
    # Collect both quality metrics and operational metrics so different normalization
    # strategies can be compared on correctness and runtime behavior.
    predictions = []
    accuracy_scores = []
    completeness_scores = []
    exact_match_scores = []
    latencies = []
    latency_attempts = []
    failures = 0
    total_requests = 0
    total_input_tokens = 0.0
    total_output_tokens = 0.0
    total_tokens = 0.0
    total_estimated_cost = 0.0

    total_samples = len(dataset)

    for index, sample in enumerate(dataset, start=1):
        sample_latencies = []
        usage_deltas = []
        prediction = None

        for attempt in range(BENCHMARK_RUNS):
            if pipeline is llm_pipeline:
                clear_llm_cache()

            usage_before = snapshot_usage()
            start = time.perf_counter()
            try:
                current_prediction = pipeline(sample["input"])
            except Exception as error:
                # Convert pipeline failures into structured records so the benchmark
                # can continue and report the failure rate.
                current_prediction = {"error": str(error)}
                if attempt == 0:
                    failures += 1
            latency = time.perf_counter() - start
            usage_after = snapshot_usage()

            sample_latencies.append(latency)
            latency_attempts.append(latency)
            usage_deltas.append(
                {
                    "requests": usage_after["requests"] - usage_before["requests"],
                    "input_tokens": usage_after["input_tokens"] - usage_before["input_tokens"],
                    "output_tokens": usage_after["output_tokens"] - usage_before["output_tokens"],
                    "total_tokens": usage_after["total_tokens"] - usage_before["total_tokens"],
                    "estimated_cost_usd": (
                        usage_after["estimated_cost_usd"] - usage_before["estimated_cost_usd"]
                    ),
                }
            )

            if attempt == 0:
                prediction = current_prediction

        latencies.append(sum(sample_latencies) / len(sample_latencies))

        total_requests += sum(item["requests"] for item in usage_deltas) / len(usage_deltas)
        total_input_tokens += sum(item["input_tokens"] for item in usage_deltas) / len(usage_deltas)
        total_output_tokens += sum(item["output_tokens"] for item in usage_deltas) / len(usage_deltas)
        total_tokens += sum(item["total_tokens"] for item in usage_deltas) / len(usage_deltas)
        total_estimated_cost += (
            sum(item["estimated_cost_usd"] for item in usage_deltas) / len(usage_deltas)
        )

        record = {"input": sample["input"], "ground_truth": sample["ground_truth"], "prediction": prediction}
        predictions.append(record)

        accuracy_scores.append(accuracy(prediction, sample["ground_truth"]))
        completeness_scores.append(completeness(prediction, sample["ground_truth"]))
        exact_match_scores.append(exact_match(prediction, sample["ground_truth"]))

        if sample_callback is not None:
            sample_callback(index, total_samples, record, predictions)

    total = len(dataset) or 1
    metrics = {
        "accuracy": sum(accuracy_scores) / total,
        "completeness": sum(completeness_scores) / total,
        "exact_match": sum(exact_match_scores) / total,
        "latency": sum(latencies) / total,
        "latency_stddev": statistics.pstdev(latency_attempts) if len(latency_attempts) > 1 else 0.0,
        "failure_rate": failures / total,
        "benchmark_runs": BENCHMARK_RUNS,
        "llm_requests": total_requests / total,
        "prompt_tokens": total_input_tokens / total,
        "completion_tokens": total_output_tokens / total,
        "total_tokens": total_tokens / total,
        "estimated_cost_usd": total_estimated_cost / total,
    }
    if pipeline in {llm_pipeline, hybrid_pipeline}:
        metrics["llm_model"] = get_llm_model()
    return metrics, predictions


def run_evaluation(datasets, progress_callback=None, sample_callback=None):
    # Execute every pipeline against every dataset to produce a complete comparison matrix.
    results = {}

    for dataset_name, dataset in datasets.items():
        results[dataset_name] = {}
        for pipeline_name, pipeline in PIPELINES.items():
            if progress_callback is not None:
                progress_callback(dataset_name, pipeline_name, "started")

            metrics, predictions = evaluate_pipeline(
                pipeline,
                dataset,
                sample_callback=build_sample_callback(sample_callback, dataset_name, pipeline_name),
            )
            results[dataset_name][pipeline_name] = {
                "metrics": metrics,
                "predictions": predictions,
            }

            if progress_callback is not None:
                progress_callback(dataset_name, pipeline_name, "finished")

    return results
