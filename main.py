from evaluation.evaluator import run_evaluation
from utils.io_helpers import (
    OUTPUT_DIR,
    load_datasets,
    print_results,
    save_pipeline_predictions,
    save_summary,
)
from utils.llm_client import close_client


def on_pipeline_progress(dataset_name, pipeline_name, status):
    if status == "started":
        print(f"\nRunning {pipeline_name} on {dataset_name}...")
    else:
        print(f"Finished {pipeline_name} on {dataset_name}")


def on_sample_processed(dataset_name, pipeline_name, index, total, _record, predictions):
    print(f"  processed {index}/{total}")
    save_pipeline_predictions(dataset_name, pipeline_name, predictions)


def main():
    # The main workflow runs the benchmark, stores per-pipeline predictions, and
    # writes a compact metrics summary for later inspection.
    OUTPUT_DIR.mkdir(exist_ok=True)
    results = run_evaluation(
        load_datasets(),
        progress_callback=on_pipeline_progress,
        sample_callback=on_sample_processed,
    )
    save_summary(results)
    print_results(results)


if __name__ == "__main__":
    try:
        main()
    finally:
        close_client()
