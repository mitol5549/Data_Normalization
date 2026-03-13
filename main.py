import json
from pathlib import Path

from evaluation.evaluator import run_evaluation
from utils.llm_client import close_client, get_llm_status


DATASET_FILES = {
    "devices": Path("datasets/devices.json"),
    "mobile_plans": Path("datasets/mobile_plans.json"),
}
OUTPUT_DIR = Path("outputs")


def load_datasets():
    datasets = {}
    for name, path in DATASET_FILES.items():
        with path.open(encoding="utf-8") as file:
            datasets[name] = json.load(file)
    return datasets


def save_summary(results):
    summary = {
        dataset_name: {
            pipeline_name: payload["metrics"]
            for pipeline_name, payload in dataset_results.items()
        }
        for dataset_name, dataset_results in results.items()
    }

    (OUTPUT_DIR / "evaluation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_pipeline_predictions(dataset_name, pipeline_name, predictions):
    output_path = OUTPUT_DIR / f"{dataset_name}_{pipeline_name}_normalized.json"
    output_path.write_text(
        json.dumps(predictions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def on_pipeline_progress(dataset_name, pipeline_name, status):
    if status == "started":
        print(f"\nRunning {pipeline_name} on {dataset_name}...")
    else:
        print(f"Finished {pipeline_name} on {dataset_name}")


def on_sample_processed(dataset_name, pipeline_name, index, total, _record, predictions):
    print(f"  processed {index}/{total}")
    save_pipeline_predictions(dataset_name, pipeline_name, predictions)


def print_results(results):
    llm_status = get_llm_status()
    print(f"\nLLM mode: {llm_status['mode']}")
    print(f"LLM status: {llm_status['reason']}\n")

    for dataset_name, dataset_results in results.items():
        print(dataset_name)
        for pipeline_name, payload in dataset_results.items():
            print(f"  {pipeline_name}")
            for key, value in payload["metrics"].items():
                print(f"    {key}: {value:.3f}")
        print()


def main():
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
