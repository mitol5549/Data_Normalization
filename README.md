# Data Normalization Prototype

This project compares three approaches for normalizing heterogeneous records into a shared target schema:

- `rule`
- `llm`
- `hybrid`

It currently supports two entity types:

- devices
- mobile plans

## Experiment Goal

The project is designed to compare three normalization strategies with clearly different behavior:

- `rule`: fastest and cheapest baseline, but intentionally limited to easy and explicit cases.
- `llm`: full-model extraction of the entire target schema, expected to be the most flexible and often the most accurate, but slower.
- `hybrid`: rule-first extraction followed by targeted LLM completion only for unresolved fields, expected to be faster than full LLM on partially structured inputs.

The benchmark is intentionally set up so that:

- easy datasets can be solved by deterministic mappings alone,
- medium datasets require a combination of explicit mappings and semantic recovery,
- hard datasets expose the limits of rule-based extraction and require LLM reasoning.

## Benchmark Datasets

The current benchmark uses six datasets stored in `datasets/`:

- `devices_easy.json`
- `devices_medium.json`
- `devices_hard.json`
- `mobile_plans_easy.json`
- `mobile_plans_medium.json`
- `mobile_plans_hard.json`

Their intended roles are:

- `devices_easy`: flat, explicit device records that the rule-based baseline should normalize almost perfectly.
- `devices_medium`: device records with alternative but still recognizable source keys and value formats.
- `devices_hard`: nested, noisy, partially textual, or weakly structured device records that expose the limits of deterministic extraction.
- `mobile_plans_easy`: flat and explicit tariff records that should be solved by rule-based mappings.
- `mobile_plans_medium`: mobile plan records with synonym keys, light noise, and less direct formatting.
- `mobile_plans_hard`: nested or text-heavy mobile plan records that require stronger semantic reasoning.

Each dataset file contains a list of samples with:

- `input`: the heterogeneous source record
- `ground_truth`: the expected normalized target record

## Project Structure

- `main.py` runs the full evaluation workflow and writes outputs.
- `normalization/` contains the rule-based, LLM-based, and hybrid pipelines.
- `evaluation/` contains metrics and evaluation orchestration.
- `datasets/` contains input samples and ground-truth records.
- `schemas/` contains the target schema definitions used by the pipelines.
- `utils/llm_client.py` provides OpenAI API access for the LLM-based pipelines.
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
- `tariff_name`
- `price_eur_per_month`
- `data_gb`
- `contract_months`

## Pipeline Logic

### Rule-Based Pipeline

The rule-based pipeline is intentionally simple.

- It uses deterministic source-key mappings only.
- It extracts only from explicit top-level fields.
- It normalizes matched values into the target schema types.
- It always returns the full target schema shape.
- Any field it cannot extract is returned as `None`.

This is deliberate: the rule-based baseline should solve straightforward records very quickly, but fail on nested, noisy, or semantically indirect inputs.

### LLM Pipeline

The LLM pipeline is a pure full-extraction pipeline.

- It sends the full input record to the model.
- It asks the model to return the full normalized target object.
- It accepts only target-schema fields from the model response.
- It normalizes returned values into the expected schema types.
- It does not use rule-based fallback or local heuristic fallback.

If the OpenAI client is unavailable or the model response is invalid JSON, the pipeline fails rather than silently switching to another strategy. This keeps the experiment clean: `llm` means actual LLM extraction only.

### Hybrid Pipeline

The hybrid pipeline combines both approaches in sequence.

1. Run the rule-based pipeline on the full record.
2. Identify target fields whose value is `None`.
3. Call the LLM only for those unresolved fields.
4. Merge the results so that rule-based values stay unchanged and the LLM fills only the gaps.

For partial LLM extraction, the prompt also includes already resolved rule-based fields as read-only context. This gives the model extra information for recovering missing attributes without allowing it to overwrite values that were already extracted deterministically.

This means the hybrid pipeline is not just “rule + full LLM merged later”. It is a selective LLM fallback on unresolved schema attributes.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Required for LLM and hybrid pipelines:

- `OPENAI_API_KEY` enables live OpenAI requests for the `llm` and `hybrid` pipelines.
- `OPENAI_MODEL` overrides the default model name.
- `OPENAI_TIMEOUT` sets the client timeout in seconds.

You can place them in a local `.env` file.

## Run

```bash
python3 main.py
```

The evaluation runs every dataset through all three pipelines and writes both aggregate metrics and per-sample predictions to `outputs/`.

If the OpenAI client is unavailable or the model response is invalid, the `llm` pipeline fails instead of falling back to local heuristics. The `hybrid` pipeline only depends on the LLM when rule-based extraction leaves unresolved fields.

## Outputs

Running the project creates:

- `outputs/evaluation_summary.json`
- `outputs/devices_easy_rule_normalized.json`
- `outputs/devices_easy_llm_normalized.json`
- `outputs/devices_easy_hybrid_normalized.json`
- `outputs/devices_medium_rule_normalized.json`
- `outputs/devices_medium_llm_normalized.json`
- `outputs/devices_medium_hybrid_normalized.json`
- `outputs/devices_hard_rule_normalized.json`
- `outputs/devices_hard_llm_normalized.json`
- `outputs/devices_hard_hybrid_normalized.json`
- `outputs/mobile_plans_easy_rule_normalized.json`
- `outputs/mobile_plans_easy_llm_normalized.json`
- `outputs/mobile_plans_easy_hybrid_normalized.json`
- `outputs/mobile_plans_medium_rule_normalized.json`
- `outputs/mobile_plans_medium_llm_normalized.json`
- `outputs/mobile_plans_medium_hybrid_normalized.json`
- `outputs/mobile_plans_hard_rule_normalized.json`
- `outputs/mobile_plans_hard_llm_normalized.json`
- `outputs/mobile_plans_hard_hybrid_normalized.json`

Each per-pipeline output file stores:

- the original input record,
- the ground-truth normalized record,
- the pipeline prediction.

`outputs/evaluation_summary.json` stores the aggregate metrics for each dataset and pipeline:

- `accuracy`
- `completeness`
- `exact_match`
- `latency`
- `failure_rate`

## Notes

- The rule-based pipeline uses deterministic top-level source-field mappings and value normalization, and returns `None` for target fields it cannot fill.
- The LLM pipeline asks the model for the full target object and validates the returned fields against the target schema.
- The hybrid pipeline runs rule-based extraction first and sends only `None` target fields to the LLM for completion.
- Because hybrid still pays for an LLM call when many fields are unresolved, it is usually faster than full LLM on easy and medium cases, but not guaranteed to be faster on every hard case.
