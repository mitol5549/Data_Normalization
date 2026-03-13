import json
from functools import lru_cache

from normalization.config import TARGET_FIELDS, detect_entity, map_known_fields, normalize_value
from utils.llm_client import ask_llm_json


def build_prompt(entity, data):
    # Keep the prompt constrained to the allowed schema fields so the model is less
    # likely to invent extra attributes.
    fields = ", ".join(TARGET_FIELDS[entity])
    return (
        f"Normalize this {entity} record into JSON.\n"
        f"Allowed fields: {fields}\n"
        "Return JSON only.\n"
        f"Record: {json.dumps(data, ensure_ascii=True)}"
    )


def semantic_fallback(entity, data):
    return map_known_fields(entity, data)


@lru_cache(maxsize=256)
def _llm_pipeline_cached(payload):
    # Cache by serialized payload so repeated evaluations of the same record do not
    # trigger duplicate API calls.
    data = json.loads(payload)
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    response = ask_llm_json(build_prompt(entity, data))
    if isinstance(response, dict):
        normalized = {"entity": entity}
        # Only accept fields that exist in the target schema and re-normalize them locally.
        for field in TARGET_FIELDS[entity]:
            if field in response:
                normalized[field] = normalize_value(field, response[field])
        if len(normalized) > 1:
            return normalized

    # Fall back to deterministic mapping whenever the LLM is unavailable or returns
    # invalid / incomplete JSON.
    return semantic_fallback(entity, data)


def llm_pipeline(data):
    # Serialize with stable ordering to make the cache key deterministic.
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return _llm_pipeline_cached(payload)
