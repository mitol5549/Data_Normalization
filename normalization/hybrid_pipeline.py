from normalization.config import TARGET_FIELDS
from normalization.llm_pipeline import extract_fields_with_llm
from normalization.rule_based_pipeline import rule_pipeline


def hybrid_pipeline(data):
    # Resolve easy fields deterministically first, then ask the LLM only for the
    # target attributes that remain empty.
    rule_result = rule_pipeline(data)
    entity = rule_result.get("entity")
    if entity is None:
        raise ValueError("Unable to detect entity type")

    missing_fields = [field for field in TARGET_FIELDS[entity] if rule_result.get(field) is None]
    if not missing_fields:
        return rule_result

    known_fields = {
        field: rule_result[field]
        for field in TARGET_FIELDS[entity]
        if rule_result.get(field) is not None
    }
    llm_result = extract_fields_with_llm(entity, data, missing_fields, known_fields=known_fields)
    merged = {"entity": entity}
    for field in TARGET_FIELDS[entity]:
        if rule_result.get(field) is not None:
            merged[field] = rule_result[field]
        else:
            merged[field] = llm_result.get(field)

    return merged
