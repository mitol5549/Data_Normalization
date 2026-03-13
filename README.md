# Data Normalization Prototype

Простой прототип для сравнения трех подходов нормализации гетерогенных данных:

- `rule`
- `llm`
- `hybrid`

Проект приводит два типа данных к упрощенной целевой схеме:

- устройства
- мобильные тарифы

## Структура

- `datasets/devices.json` - примеры устройств
- `datasets/mobile_plans.json` - примеры тарифов
- `outputs/` - готовые нормализованные данные и сводка метрик

## Целевые атрибуты

Устройства:
- `brand`
- `model`
- `ram_gb`
- `storage_gb`
- `price_eur`

Тарифы:
- `provider`
- `plan_name`
- `monthly_price_eur`
- `data_gb`
- `data_unlimited`
- `contract_months`

## Запуск

```bash
python3 main.py
```

Если в `.env` есть `OPENAI_API_KEY`, то `llm` и `hybrid` используют API OpenAI. Иначе они переходят в локальный fallback-режим.

## Выходные файлы

После запуска создаются:

- `outputs/evaluation_summary.json`
- `outputs/devices_rule_normalized.json`
- `outputs/devices_llm_normalized.json`
- `outputs/devices_hybrid_normalized.json`
- `outputs/mobile_plans_rule_normalized.json`
- `outputs/mobile_plans_llm_normalized.json`
- `outputs/mobile_plans_hybrid_normalized.json`
