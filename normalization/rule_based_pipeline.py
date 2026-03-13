from normalization.config import SOURCE_MAPPINGS, canonicalize_key, detect_entity, normalize_value


def rule_pipeline(data):
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    normalized = {"entity": entity}
    mapping = SOURCE_MAPPINGS[entity]

    for source_key, value in data.items():
        target_key = mapping.get(canonicalize_key(source_key))
        if target_key is not None:
            normalized[target_key] = normalize_value(target_key, value)

    if entity == "mobile_plan" and normalized.get("data_unlimited") is None:
        normalized["data_unlimited"] = any("unlimited" in str(value).lower() for value in data.values())

    return normalized
