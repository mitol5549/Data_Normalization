import re

from normalization.mappings import SEMANTIC_SOURCE_MAPPINGS


def canonicalize_key(key):
    # Normalize external field names so "brand name", "brand-name", and "brand_name"
    # can all be matched through the same mapping table.
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def iter_leaf_fields(data, path=()):
    if isinstance(data, dict):
        for key, value in data.items():
            yield from iter_leaf_fields(value, path + (str(key),))
        return

    yield path, data


def iter_top_level_fields(data):
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        if isinstance(value, dict):
            continue
        yield (str(key),), value


def candidate_source_keys(path):
    canonical_parts = [canonicalize_key(part) for part in path if canonicalize_key(part)]
    if not canonical_parts:
        return []

    candidates = ["_".join(canonical_parts)]
    if len(canonical_parts) >= 2:
        candidates.append("_".join(canonical_parts[-2:]))
    candidates.append(canonical_parts[-1])
    return list(dict.fromkeys(candidates))


def detect_entity(data, mappings=SEMANTIC_SOURCE_MAPPINGS, nested=True):
    # Infer the record type from how many source keys match each entity mapping.
    scores = {"device": 0, "mobile_plan": 0}
    field_iterator = iter_leaf_fields(data) if nested else iter_top_level_fields(data)

    for path, _ in field_iterator:
        for source_key in candidate_source_keys(path):
            for entity, mapping in mappings.items():
                if source_key in mapping:
                    scores[entity] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None
