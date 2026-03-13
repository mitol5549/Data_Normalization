from normalization.config import detect_entity, map_known_fields


def rule_pipeline(data):
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    # Start with deterministic source-to-target mapping before applying
    # entity-specific heuristics.
    normalized = map_known_fields(entity, data)

    # Unlimited plans often omit a numeric allowance, so infer the flag from raw values.
    if entity == "mobile_plan" and normalized.get("data_unlimited") is None:
        normalized["data_unlimited"] = any("unlimited" in str(value).lower() for value in data.values())

    return normalized
