import json

from normalization.rule_based_pipeline import (
    PLAN_MAPPING,
    DEVICE_MAPPING,
    canonicalize_key,
    detect_entity,
    normalize_value,
)
from utils.llm_client import ask_llm_json


TARGET_FIELDS = {
    "device": [
        "brand",
        "model",
        "device_type",
        "release_year",
        "storage_gb",
        "ram_gb",
        "screen_size_inch",
        "battery_mah",
        "os",
        "price_eur",
    ],
    "mobile_plan": [
        "provider",
        "plan_name",
        "monthly_price_eur",
        "data_gb",
        "data_unlimited",
        "contract_months",
        "network_type",
        "sms_included",
        "calls_included",
        "roaming_eu",
    ],
}


SEMANTIC_FIELD_HINTS = {
    "device": {
        "brand": ["brand", "maker", "manufacturer", "vendor"],
        "model": ["model", "device", "product"],
        "device_type": ["type", "category"],
        "release_year": ["year", "release"],
        "storage_gb": ["storage", "rom", "capacity"],
        "ram_gb": ["ram", "memory"],
        "screen_size_inch": ["screen", "display", "size"],
        "battery_mah": ["battery", "mah"],
        "os": ["os", "platform", "system"],
        "price_eur": ["price", "cost", "eur"],
    },
    "mobile_plan": {
        "provider": ["provider", "carrier", "operator", "company"],
        "plan_name": ["plan", "tariff", "package"],
        "monthly_price_eur": ["price", "monthly", "fee", "cost"],
        "data_gb": ["data", "internet", "allowance", "limit"],
        "data_unlimited": ["unlimited"],
        "contract_months": ["contract", "duration", "term", "commitment"],
        "network_type": ["network", "generation", "5g", "4g"],
        "sms_included": ["sms", "text"],
        "calls_included": ["calls", "voice", "minutes"],
        "roaming_eu": ["roaming", "eu"],
    },
}


def _build_prompt(entity, data):
    fields = TARGET_FIELDS[entity]
    schema_description = ", ".join(fields)
    return (
        "Normalize the source record to the target schema.\n"
        f"Entity: {entity}\n"
        f"Allowed output fields: {schema_description}\n"
        "Return valid JSON with the normalized attributes only. "
        "Do not include explanations or markdown.\n"
        f"Source record: {json.dumps(data, ensure_ascii=True)}"
    )


def _semantic_fallback(entity, data):
    normalized = {"entity": entity}
    hints = SEMANTIC_FIELD_HINTS[entity]
    exact_mapping = DEVICE_MAPPING if entity == "device" else PLAN_MAPPING

    for source_key, value in data.items():
        canonical_key = canonicalize_key(source_key)
        target_key = exact_mapping.get(canonical_key)

        if target_key is None:
            best_field = None
            best_score = 0

            for field, aliases in hints.items():
                score = sum(alias in canonical_key for alias in aliases)
                if score > best_score:
                    best_field = field
                    best_score = score

            target_key = best_field if best_score > 0 else None

        if target_key is not None:
            normalized[target_key] = normalize_value(target_key, value)

    return normalized


def llm_pipeline(data):
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type from the input record")

    response = ask_llm_json(_build_prompt(entity, data))
    if isinstance(response, dict):
        normalized = {"entity": entity}
        for field in TARGET_FIELDS[entity]:
            if field in response:
                normalized[field] = normalize_value(field, response[field])
        if len(normalized) > 1:
            return normalized

    return _semantic_fallback(entity, data)
