import json
from functools import lru_cache

from normalization.schema import TARGET_FIELDS
from normalization.source_fields import detect_entity
from normalization.value_normalization import normalize_value
from utils.llm_client import ask_llm_json


def build_prompt(entity, data, fields=None, known_fields=None):
    # Keep the prompt constrained to the allowed schema fields so the model is less
    # likely to invent extra attributes.
    selected_fields = TARGET_FIELDS[entity] if fields is None else list(fields)
    fields_text = ", ".join(selected_fields)
    if fields is None:
        task = "Extract the full normalized target object."
        known_fields_text = ""
    else:
        task = "Extract only the missing target fields listed below."
        known_fields_payload = json.dumps(known_fields or {}, ensure_ascii=True)
        known_fields_text = (
            f"Known fields already resolved by rules: {known_fields_payload}\n"
            "Use these values as context only.\n"
            "Do not return them and do not change them.\n"
        )
    return (
        f"Normalize this {entity} record into JSON.\n"
        f"{task}\n"
        f"Allowed fields: {fields_text}\n"
        "Do not return any fields outside this list.\n"
        "If a field cannot be determined from the record, return it as null.\n"
        f"{known_fields_text}"
        "Return JSON only.\n"
        f"Record: {json.dumps(data, ensure_ascii=True)}"
    )


def extract_fields_with_llm(entity, data, fields, known_fields=None):
    selected_fields = list(fields)
    if not selected_fields:
        return {"entity": entity}

    response = ask_llm_json(build_prompt(entity, data, selected_fields, known_fields=known_fields))
    if not isinstance(response, dict):
        raise ValueError("LLM did not return valid JSON")

    normalized = {"entity": entity}
    for field in selected_fields:
        normalized[field] = normalize_value(field, response.get(field))
    return normalized


@lru_cache(maxsize=256)
def _llm_pipeline_cached(payload):
    # Cache by serialized payload so repeated evaluations of the same record do not
    # trigger duplicate API calls.
    data = json.loads(payload)
    entity = detect_entity(data, nested=True)
    if entity is None:
        raise ValueError("Unable to detect entity type")

    # The LLM pipeline extracts the full target object itself.
    return extract_fields_with_llm(entity, data, TARGET_FIELDS[entity])


def llm_pipeline(data):
    # Serialize with stable ordering to make the cache key deterministic.
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return _llm_pipeline_cached(payload)


def clear_llm_cache():
    _llm_pipeline_cached.cache_clear()
