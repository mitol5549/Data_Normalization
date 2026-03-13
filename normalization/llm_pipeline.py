import json
from functools import lru_cache

from normalization.config import TARGET_FIELDS, SOURCE_MAPPINGS, canonicalize_key, detect_entity, normalize_value
from utils.llm_client import ask_llm_json


def build_prompt(entity, data):
    fields = ", ".join(TARGET_FIELDS[entity])
    return (
        f"Normalize this {entity} record into JSON.\n"
        f"Allowed fields: {fields}\n"
        "Return JSON only.\n"
        f"Record: {json.dumps(data, ensure_ascii=True)}"
    )


def semantic_fallback(entity, data):
    normalized = {"entity": entity}
    mapping = SOURCE_MAPPINGS[entity]

    for source_key, value in data.items():
        target_key = mapping.get(canonicalize_key(source_key))
        if target_key is not None:
            normalized[target_key] = normalize_value(target_key, value)

    return normalized


@lru_cache(maxsize=256)
def _llm_pipeline_cached(payload):
    data = json.loads(payload)
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    response = ask_llm_json(build_prompt(entity, data))
    if isinstance(response, dict):
        normalized = {"entity": entity}
        for field in TARGET_FIELDS[entity]:
            if field in response:
                normalized[field] = normalize_value(field, response[field])
        if len(normalized) > 1:
            return normalized

    return semantic_fallback(entity, data)


def llm_pipeline(data):
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return _llm_pipeline_cached(payload)
