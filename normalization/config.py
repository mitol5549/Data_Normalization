import re


TARGET_FIELDS = {
    "device": ["brand", "model", "ram_gb", "storage_gb", "price_eur"],
    "mobile_plan": [
        "provider",
        "plan_name",
        "monthly_price_eur",
        "data_gb",
        "data_unlimited",
        "contract_months",
    ],
}


SOURCE_MAPPINGS = {
    "device": {
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
        "capacity": "storage_gb",
        "rom": "storage_gb",
        "price": "price_eur",
        "price_eur": "price_eur",
        "cost": "price_eur",
    },
    "mobile_plan": {
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
    },
}


BOOLEAN_TRUE = {"yes", "true", "included", "unlimited", "1"}
BOOLEAN_FALSE = {"no", "false", "0"}


def canonicalize_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def extract_number(value):
    text = str(value).strip().replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    if match:
        return float(match.group())
    return None


def normalize_value(target_key, value):
    if value is None:
        return None

    if target_key in {"ram_gb", "storage_gb", "contract_months"}:
        number = extract_number(value)
        return int(number) if number is not None else None

    if target_key in {"price_eur", "monthly_price_eur", "data_gb"}:
        text = str(value).strip().lower()
        if target_key == "data_gb" and "unlimited" in text:
            return None
        return extract_number(value)

    if target_key == "data_unlimited":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in BOOLEAN_TRUE:
            return True
        if text in BOOLEAN_FALSE:
            return False
        return None

    return str(value).strip() or None


def detect_entity(data):
    scores = {"device": 0, "mobile_plan": 0}

    for source_key in data:
        key = canonicalize_key(source_key)
        for entity, mapping in SOURCE_MAPPINGS.items():
            if key in mapping:
                scores[entity] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None
