from normalization.mappings import RULE_SOURCE_MAPPINGS, SEMANTIC_SOURCE_MAPPINGS
from normalization.schema import SCHEMA_DIR, SCHEMA_FILES, TARGET_FIELDS, load_target_fields
from normalization.source_fields import (
    candidate_source_keys,
    canonicalize_key,
    detect_entity,
    iter_leaf_fields,
    iter_top_level_fields,
)
from normalization.value_normalization import (
    ensure_all_target_fields,
    extract_memory_gb,
    extract_number,
    infer_device_specs,
    map_known_fields,
    normalize_value,
)
