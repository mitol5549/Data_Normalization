# Data Normalization Prototype

Research prototype for comparing three normalization strategies on heterogeneous product data:

- `rule`: deterministic schema mapping and value normalization
- `llm`: LLM-first normalization with a semantic fallback when no API key is available
- `hybrid`: rule-based extraction with LLM-assisted gap filling

## Project goals

The project converts heterogeneous source records into one target schema and exposes metrics that are useful for an empirical comparison in a scientific paper:

- field-level accuracy
- completeness
- exact-match rate
- average latency
- failure rate

## Run

```bash
pip install -r requirements.txt
python3 main.py
```

If `OPENAI_API_KEY` is set, the LLM pipeline calls the OpenAI API. Without it, the code still runs by using a local semantic fallback so the benchmark remains executable.

## Dataset

`datasets/device_dataset.json` now contains both `device` and `mobile_plan` samples with heterogeneous source keys and value formats. This gives you a better baseline for comparing:

- how robust pure rules are to schema variation
- where an LLM helps with semantic interpretation
- whether a hybrid pipeline improves completeness without sacrificing precision

## Suggested next research steps

1. Split the dataset into train, validation and held-out evaluation subsets.
2. Add more adversarial samples with missing keys, ambiguous labels and multilingual field names.
3. Log token usage and API cost for the LLM and hybrid pipelines.
4. Report per-entity metrics, not just aggregate scores.
