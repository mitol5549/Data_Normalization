import json
import re
from pathlib import Path


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMA_FILES = {
    "device": SCHEMA_DIR / "target_schema_devices.json",
    "mobile_plan": SCHEMA_DIR / "target_schema_mobile_plans.json",
}


RULE_SOURCE_MAPPINGS = {
    "device": {
        "manufacturer": "brand",
        "brand": "brand",
        "brand_name": "brand",
        "maker": "brand",
        "vendor": "brand",
        "device_model": "model",
        "model": "model",
        "model_name": "model",
        "product_name": "model",
        "ram": "ram_gb",
        "memory_ram": "ram_gb",
        "memory": "ram_gb",
        "storage": "storage_gb",
        "internal_storage": "storage_gb",
        "capacity": "storage_gb",
        "rom": "storage_gb",
        "price": "price_eur",
        "price_eur": "price_eur",
        "cost": "price_eur",
    },
    "mobile_plan": {
        "carrier": "provider",
        "operator": "provider",
        "provider": "provider",
        "company": "provider",
        "tariff_name": "tariff_name",
        "plan": "tariff_name",
        "plan_name": "tariff_name",
        "tariff": "tariff_name",
        "price": "price_eur_per_month",
        "monthly_fee": "price_eur_per_month",
        "monthly_price": "price_eur_per_month",
        "fee": "price_eur_per_month",
        "data_volume": "data_gb",
        "data_limit": "data_gb",
        "data": "data_gb",
        "data_gb": "data_gb",
        "internet": "data_gb",
        "allowance": "data_gb",
        "contract_length": "contract_months",
        "duration": "contract_months",
        "term": "contract_months",
        "commitment": "contract_months",
        "contract": "contract_months",
    },
}


SEMANTIC_SOURCE_MAPPINGS = {
    "device": {
        **RULE_SOURCE_MAPPINGS["device"],
        "device_info_maker": "brand",
        "device_brand_name": "brand",
        "phone": "model",
        "product": "model",
        "name": "model",
        "device_info_name": "model",
        "device_model_name": "model",
        "ram_memory": "ram_gb",
        "hardware_specs_memory": "ram_gb",
        "storage_capacity": "storage_gb",
        "disk": "storage_gb",
        "amount": "price_eur",
        "price_tag": "price_eur",
        "pricing_amount": "price_eur",
    },
    "mobile_plan": {
        **RULE_SOURCE_MAPPINGS["mobile_plan"],
        "provider_name": "provider",
        "name": "provider",
        "carrier_info_name": "provider",
        "title": "tariff_name",
        "offer": "tariff_name",
        "tariff_details_title": "tariff_name",
        "price_info": "price_eur_per_month",
        "tariff_details_price_info": "price_eur_per_month",
        "internet_data": "data_gb",
        "internet_package": "data_gb",
        "data_package": "data_gb",
        "tariff_details_internet_package": "data_gb",
        "contract_type": "contract_months",
        "metadata_contract": "contract_months",
    },
}


def load_target_fields():
    target_fields = {}
    for entity, schema_path in SCHEMA_FILES.items():
        # Keep target fields in sync with the JSON schemas instead of duplicating them in code.
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        target_fields[entity] = [attribute["name"] for attribute in schema["attributes"]]
    return target_fields


TARGET_FIELDS = load_target_fields()


def canonicalize_key(key):
    # Normalize external field names so "brand name", "brand-name", and "brand_name"
    # can all be matched through the same mapping table.
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def iter_leaf_fields(data, path=()):
    if isinstance(data, dict):
        for key, value in data.items():
            yield from iter_leaf_fields(value, path + (str(key),))
        return

    yield path, data


def iter_top_level_fields(data):
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        if isinstance(value, dict):
            continue
        yield (str(key),), value


def candidate_source_keys(path):
    canonical_parts = [canonicalize_key(part) for part in path if canonicalize_key(part)]
    if not canonical_parts:
        return []

    candidates = ["_".join(canonical_parts)]
    if len(canonical_parts) >= 2:
        candidates.append("_".join(canonical_parts[-2:]))
    candidates.append(canonical_parts[-1])
    return list(dict.fromkeys(candidates))


def extract_number(value):
    # Extract the first numeric token from noisy strings such as "39.99 EUR" or "8 GB".
    text = str(value).strip().replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    if match:
        return float(match.group())
    return None


def extract_memory_gb(value):
    text = str(value).strip().lower().replace(",", ".")
    match = re.search(r"(\d+(\.\d+)?)\s*(tb|gb|mb)?", text)
    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(3) or "gb"
    if unit == "tb":
        return int(number * 1024)
    if unit == "mb":
        return int(number / 1024)
    return int(number)


def infer_device_specs(data):
    inferred = {}

    for _, value in iter_leaf_fields(data):
        text = str(value).strip().lower().replace(",", ".")

        if "ram" in text:
            ram_match = re.search(r"(\d+(\.\d+)?)\s*(tb|gb|mb)\s*ram", text)
            if ram_match:
                inferred["ram_gb"] = extract_memory_gb(ram_match.group(0))

        if "storage" in text:
            storage_match = re.search(r"(\d+(\.\d+)?)\s*(tb|gb|mb)\s*storage", text)
            if storage_match:
                inferred["storage_gb"] = extract_memory_gb(storage_match.group(0))

        if "ram" in text and "storage" in text:
            ram_match = re.search(r"(\d+(\.\d+)?)\s*(tb|gb|mb)\s*ram", text)
            storage_match = re.search(r"(\d+(\.\d+)?)\s*(tb|gb|mb)\s*storage", text)
            if ram_match and "ram_gb" not in inferred:
                inferred["ram_gb"] = extract_memory_gb(ram_match.group(0))
            if storage_match and "storage_gb" not in inferred:
                inferred["storage_gb"] = extract_memory_gb(storage_match.group(0))

    return inferred


def normalize_value(target_key, value):
    # Coerce heterogeneous input values into the types expected by the target schema.
    if value is None:
        return None

    if target_key in {"ram_gb", "storage_gb", "contract_months"}:
        if target_key in {"ram_gb", "storage_gb"}:
            return extract_memory_gb(value)
        number = extract_number(value)
        return int(number) if number is not None else None

    if target_key in {"price_eur", "price_eur_per_month", "data_gb"}:
        text = str(value).strip().lower()
        if target_key == "data_gb" and "unlimited" in text:
            return None
        return extract_number(value)

    return str(value).strip() or None


def ensure_all_target_fields(entity, normalized):
    completed = {"entity": entity}
    for field in TARGET_FIELDS[entity]:
        completed[field] = normalized.get(field)
    return completed


def map_known_fields(entity, data, mappings=SEMANTIC_SOURCE_MAPPINGS, nested=True, infer_device=False):
    # Apply only deterministic field mappings here. Pipelines can layer additional
    # heuristics or LLM output on top of this baseline normalization.
    normalized = {"entity": entity}
    mapping = mappings[entity]
    field_iterator = iter_leaf_fields(data) if nested else iter_top_level_fields(data)

    for path, value in field_iterator:
        for source_key in candidate_source_keys(path):
            target_key = mapping.get(source_key)
            if target_key is not None:
                normalized[target_key] = normalize_value(target_key, value)
                break

    if entity == "device" and infer_device:
        for target_key, value in infer_device_specs(data).items():
            normalized.setdefault(target_key, value)

    return normalized


def detect_entity(data, mappings=SEMANTIC_SOURCE_MAPPINGS, nested=True):
    # Infer the record type from how many source keys match each entity mapping.
    scores = {"device": 0, "mobile_plan": 0}
    field_iterator = iter_leaf_fields(data) if nested else iter_top_level_fields(data)

    for path, _ in field_iterator:
        for source_key in candidate_source_keys(path):
            for entity, mapping in mappings.items():
                if source_key in mapping:
                    scores[entity] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None
