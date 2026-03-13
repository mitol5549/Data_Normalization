import json
from pathlib import Path

from evaluation.evaluator import run_evaluation


dataset_path = Path("datasets/device_dataset.json")
with dataset_path.open(encoding="utf-8") as file:
    dataset = json.load(file)

results = run_evaluation(dataset)

print(f"\nEvaluation results for {len(dataset)} samples:\n")

for pipeline, metrics in results.items():
    print(pipeline)
    for key, value in metrics.items():
        print(f"  {key}: {value:.3f}")
    print()
