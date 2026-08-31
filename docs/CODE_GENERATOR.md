# Code Generator Agent — Design (Phase 4)

## Goal
Emit a **reproducible Python script** that mirrors what the pipeline did, so users can re-run offline without the API.

## Principles
1. Script is plain Python 3.11+ (pandas + sklearn only in Phase 4).
2. Reflects actual steps that ran (from pipeline `results`), not a generic template only.
3. No secrets, no network calls in the generated script.
4. JSON-safe: script returned as a string field in the agent result.

## Inputs
- `results`: list of public step results from the supervisor
- `context`: may include `target_column`, `feature_columns`, source filename

## Output
```json
{
  "status": "ok",
  "agent": "code_generator",
  "language": "python",
  "script": "# -*- coding: utf-8 -*-\n...",
  "filename_suggestion": "zyntra_pipeline_repro.py",
  "steps_covered": ["data_loader", "cleaner", ...]
}
```

## Pipeline position
Usually **last** step:
```text
... → modeler → interpretability → code_generator
```
