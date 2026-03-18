import json
from pathlib import Path

from utils.llm_client import get_llm_status


DATASET_DIR = Path("datasets")
OUTPUT_DIR = Path("outputs")


def load_datasets():
    # Load all benchmark datasets once and keep the rest of the application independent
    # from file-system details.
    datasets = {}
    for path in sorted(DATASET_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            datasets[path.stem] = json.load(file)
    return datasets


def save_summary(results):
    # Persist only the aggregate metrics in a compact summary file.
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
    # Save incremental pipeline output so intermediate results are available even
    # before the full evaluation finishes.
    output_path = OUTPUT_DIR / f"{dataset_name}_{pipeline_name}_normalized.json"
    output_path.write_text(
        json.dumps(predictions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def print_results(results):
    # Print execution mode first because LLM-based pipelines depend on external
    # API availability and may fail when the client is not configured.
    llm_status = get_llm_status()
    print(f"\nLLM mode: {llm_status['mode']}")
    print(f"LLM status: {llm_status['reason']}\n")

    for dataset_name, dataset_results in results.items():
        print(dataset_name)
        for pipeline_name, payload in dataset_results.items():
            print(f"  {pipeline_name}")
            for key, value in payload["metrics"].items():
                if isinstance(value, int) and not isinstance(value, bool):
                    print(f"    {key}: {value}")
                elif isinstance(value, float):
                    print(f"    {key}: {value:.3f}")
                else:
                    print(f"    {key}: {value}")
        print()
