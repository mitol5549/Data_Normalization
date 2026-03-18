from normalization.mappings import RULE_SOURCE_MAPPINGS
from normalization.source_fields import detect_entity
from normalization.value_normalization import ensure_all_target_fields, map_known_fields


def rule_pipeline(data):
    entity = detect_entity(data, mappings=RULE_SOURCE_MAPPINGS, nested=False)
    if entity is None:
        # Keep extraction intentionally simple, but avoid failing the whole
        # pipeline when the record shape is nested or noisy.
        entity = detect_entity(data, mappings=RULE_SOURCE_MAPPINGS, nested=True)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    # Keep the rule-based pipeline intentionally narrow: it only handles flat,
    # pre-defined source keys that can be anticipated in advance.
    normalized = map_known_fields(
        entity,
        data,
        mappings=RULE_SOURCE_MAPPINGS,
        nested=False,
        infer_device=False,
    )

    # Keep rule-based output schema-shaped so downstream pipelines can distinguish
    # explicit gaps from fields that were never considered.
    return ensure_all_target_fields(entity, normalized)
