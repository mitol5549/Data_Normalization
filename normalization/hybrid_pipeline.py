from normalization.config import TARGET_FIELDS
from normalization.llm_pipeline import llm_pipeline
from normalization.rule_based_pipeline import rule_pipeline


def hybrid_pipeline(data):
    # Run both strategies on the same input so the final result can combine the
    # determinism of rules with the broader coverage of the LLM pipeline.
    rule_result = rule_pipeline(data)
    llm_result = llm_pipeline(data)
    entity = rule_result["entity"]

    merged = {"entity": entity}
    for field in TARGET_FIELDS[entity]:
        # Prefer deterministic rule-based values and only fill remaining gaps from the LLM output.
        if field in rule_result:
            merged[field] = rule_result[field]
        elif field in llm_result:
            merged[field] = llm_result[field]

    return merged
