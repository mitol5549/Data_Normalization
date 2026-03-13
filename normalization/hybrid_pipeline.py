from normalization.config import TARGET_FIELDS
from normalization.llm_pipeline import llm_pipeline
from normalization.rule_based_pipeline import rule_pipeline


def hybrid_pipeline(data):
    rule_result = rule_pipeline(data)
    llm_result = llm_pipeline(data)
    entity = rule_result["entity"]

    merged = {"entity": entity}
    for field in TARGET_FIELDS[entity]:
        if field in rule_result:
            merged[field] = rule_result[field]
        elif field in llm_result:
            merged[field] = llm_result[field]

    return merged
