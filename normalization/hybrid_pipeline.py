from normalization.llm_pipeline import TARGET_FIELDS, llm_pipeline
from normalization.rule_based_pipeline import detect_entity, rule_pipeline


def hybrid_pipeline(data):
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type from the input record")

    rule_result = rule_pipeline(data)
    llm_result = llm_pipeline(data)

    merged = {"entity": entity}

    for field in TARGET_FIELDS[entity]:
        if field in rule_result:
            merged[field] = rule_result[field]
            continue

        if field in llm_result:
            merged[field] = llm_result[field]

    return merged
