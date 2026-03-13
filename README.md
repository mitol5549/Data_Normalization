# Data Normalization Prototype

This project compares three approaches for normalizing heterogeneous records into a shared target schema:

- `rule`
- `llm`
- `hybrid`

It currently supports two entity types:

- devices
- mobile plans

## Project Structure

- `main.py` runs the full evaluation workflow and writes outputs.
- `normalization/` contains the rule-based, LLM-based, and hybrid pipelines.
- `evaluation/` contains metrics and evaluation orchestration.
- `datasets/` contains input samples and ground-truth records.
- `schemas/` contains the target schema definitions used by the pipelines.
- `utils/llm_client.py` provides optional OpenAI API access with local fallback behavior.
- `outputs/` is generated at runtime and stores normalized predictions plus the evaluation summary.

## Target Schemas

Device fields:

- `brand`
- `model`
- `ram_gb`
- `storage_gb`
- `price_eur`

Mobile plan fields:

- `provider`
- `plan_name`
- `monthly_price_eur`
- `data_gb`
- `data_unlimited`
- `contract_months`

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional environment variables:

- `OPENAI_API_KEY` enables live OpenAI requests for the `llm` pipeline.
- `OPENAI_MODEL` overrides the default model name.
- `OPENAI_TIMEOUT` sets the client timeout in seconds.

You can place them in a local `.env` file.

## Run

```bash
python3 main.py
```

If `OPENAI_API_KEY` is missing, the project automatically falls back to local semantic mapping for the LLM-based pipeline.

## Outputs

Running the project creates:

- `outputs/evaluation_summary.json`
- `outputs/devices_rule_normalized.json`
- `outputs/devices_llm_normalized.json`
- `outputs/devices_hybrid_normalized.json`
- `outputs/mobile_plans_rule_normalized.json`
- `outputs/mobile_plans_llm_normalized.json`
- `outputs/mobile_plans_hybrid_normalized.json`

## Notes

- The rule-based pipeline uses deterministic source-field mappings and value normalization.
- The LLM pipeline validates model output against the target schema and falls back to local mapping if the response is missing or invalid.
- The hybrid pipeline prefers rule-based values and uses the LLM pipeline only to fill gaps.
