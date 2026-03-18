import re

from normalization.mappings import SEMANTIC_SOURCE_MAPPINGS
from normalization.schema import TARGET_FIELDS
from normalization.source_fields import (
    candidate_source_keys,
    iter_leaf_fields,
    iter_top_level_fields,
)


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
