import json
from pathlib import Path


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMA_FILES = {
    "device": SCHEMA_DIR / "target_schema_devices.json",
    "mobile_plan": SCHEMA_DIR / "target_schema_mobile_plans.json",
}


def load_target_fields():
    target_fields = {}
    for entity, schema_path in SCHEMA_FILES.items():
        # Keep target fields in sync with the JSON schemas instead of duplicating them in code.
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        target_fields[entity] = [attribute["name"] for attribute in schema["attributes"]]
    return target_fields


TARGET_FIELDS = load_target_fields()
