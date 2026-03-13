import time

from evaluation.metrics import accuracy, completeness, exact_match
from normalization.hybrid_pipeline import hybrid_pipeline
from normalization.llm_pipeline import llm_pipeline
from normalization.rule_based_pipeline import rule_pipeline


PIPELINES = {
    "rule": rule_pipeline,
    "llm": llm_pipeline,
    "hybrid": hybrid_pipeline,
}


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
    failures = 0

    total_samples = len(dataset)

    for index, sample in enumerate(dataset, start=1):
        start = time.perf_counter()
        try:
            prediction = pipeline(sample["input"])
        except Exception as error:
            # Convert pipeline failures into structured records so the benchmark
            # can continue and report the failure rate.
            prediction = {"error": str(error)}
            failures += 1
        latencies.append(time.perf_counter() - start)

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
        "failure_rate": failures / total,
    }
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
