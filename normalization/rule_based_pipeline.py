import re


DEVICE_MAPPING = {
    "manufacturer": "brand",
    "brand": "brand",
    "brand_name": "brand",
    "maker": "brand",
    "vendor": "brand",
    "device_model": "model",
    "model": "model",
    "model_name": "model",
    "product_name": "model",
    "ram": "ram_gb",
    "memory_ram": "ram_gb",
    "memory": "ram_gb",
    "storage": "storage_gb",
    "internal_storage": "storage_gb",
    "rom": "storage_gb",
    "capacity": "storage_gb",
    "display_size": "screen_size_inch",
    "screen": "screen_size_inch",
    "screen_size": "screen_size_inch",
    "display": "screen_size_inch",
    "battery": "battery_mah",
    "battery_capacity": "battery_mah",
    "battery_size": "battery_mah",
    "operating_system": "os",
    "os": "os",
    "platform": "os",
    "price": "price_eur",
    "price_eur": "price_eur",
    "cost": "price_eur",
    "year": "release_year",
    "release_year": "release_year",
    "device_type": "device_type",
    "category": "device_type",
}


PLAN_MAPPING = {
    "carrier": "provider",
    "operator": "provider",
    "provider": "provider",
    "company": "provider",
    "tariff_name": "plan_name",
    "plan": "plan_name",
    "plan_name": "plan_name",
    "tariff": "plan_name",
    "price": "monthly_price_eur",
    "monthly_fee": "monthly_price_eur",
    "monthly_price": "monthly_price_eur",
    "fee": "monthly_price_eur",
    "data_volume": "data_gb",
    "data_limit": "data_gb",
    "data": "data_gb",
    "internet": "data_gb",
    "allowance": "data_gb",
    "unlimited_data": "data_unlimited",
    "data_unlimited": "data_unlimited",
    "contract_length": "contract_months",
    "duration": "contract_months",
    "term": "contract_months",
    "commitment": "contract_months",
    "network": "network_type",
    "network_type": "network_type",
    "generation": "network_type",
    "sms": "sms_included",
    "text_messages": "sms_included",
    "calls": "calls_included",
    "voice": "calls_included",
    "eu_roaming": "roaming_eu",
    "roaming": "roaming_eu",
}


BOOLEAN_TRUE = {"yes", "true", "included", "unlimited", "available", "1", "y"}
BOOLEAN_FALSE = {"no", "false", "not included", "unavailable", "0", "n"}


def canonicalize_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def extract_number(value):
    text = str(value).strip().replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    if match:
        return float(match.group())
    return None


def parse_boolean(value):
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text in BOOLEAN_TRUE:
        return True
    if text in BOOLEAN_FALSE:
        return False
    return None


def normalize_device_type(value):
    text = str(value).strip().lower()
    if any(token in text for token in ["phone", "iphone", "galaxy", "pixel", "smartphone"]):
        return "smartphone"
    if any(token in text for token in ["ipad", "tablet", "tab", "pad"]):
        return "tablet"
    if any(token in text for token in ["watch", "smartwatch"]):
        return "watch"
    return "other" if text else None


def normalize_network(value):
    text = str(value).strip().upper()
    if "5" in text:
        return "5G"
    if "4" in text or "LTE" in text:
        return "4G"
    return None


def normalize_value(key, value):
    if value is None:
        return None

    if key in {"ram_gb", "storage_gb", "battery_mah", "contract_months", "release_year"}:
        number = extract_number(value)
        return int(number) if number is not None else None

    if key in {"screen_size_inch", "price_eur", "monthly_price_eur", "data_gb"}:
        text = str(value).strip().lower()
        if key == "data_gb" and "unlimited" in text:
            return None
        return extract_number(value)

    if key in {"data_unlimited", "sms_included", "calls_included", "roaming_eu"}:
        return parse_boolean(value)

    if key == "device_type":
        return normalize_device_type(value)

    if key == "network_type":
        return normalize_network(value)

    text = str(value).strip()
    return text or None


def get_mapping_for_entity(entity):
    if entity == "device":
        return DEVICE_MAPPING
    if entity == "mobile_plan":
        return PLAN_MAPPING
    raise ValueError(f"Unsupported entity: {entity}")


def detect_entity(data):
    scores = {"device": 0, "mobile_plan": 0}

    for source_key, value in data.items():
        key = canonicalize_key(source_key)

        if key in DEVICE_MAPPING:
            scores["device"] += 2
        if key in PLAN_MAPPING:
            scores["mobile_plan"] += 2

        text = str(value).lower()
        if any(token in text for token in ["mah", "inch", "android", "ios", "iphone", "galaxy"]):
            scores["device"] += 1
        if any(token in text for token in ["gb", "unlimited", "roaming", "5g", "4g"]) and key in {
            "data",
            "data_limit",
            "data_volume",
            "network",
            "generation",
            "roaming",
        }:
            scores["mobile_plan"] += 1

    best_entity = max(scores, key=scores.get)
    return best_entity if scores[best_entity] > 0 else None


def infer_missing_fields(entity, raw_data, normalized):
    if entity == "device":
        if "device_type" not in normalized:
            model = normalized.get("model") or raw_data.get("model") or raw_data.get("device_model")
            normalized["device_type"] = normalize_device_type(model)
    elif entity == "mobile_plan":
        if normalized.get("data_unlimited") is None:
            for value in raw_data.values():
                if "unlimited" in str(value).lower():
                    normalized["data_unlimited"] = True
                    break

    return normalized


def rule_pipeline(data):
    entity = detect_entity(data)
    if entity is None:
        raise ValueError("Unable to detect entity type from the input record")

    mapping = get_mapping_for_entity(entity)
    normalized = {"entity": entity}

    for source_key, value in data.items():
        canonical_key = canonicalize_key(source_key)
        target_key = mapping.get(canonical_key)
        if target_key is None:
            continue

        normalized[target_key] = normalize_value(target_key, value)

    return infer_missing_fields(entity, data, normalized)
