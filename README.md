# Structured Output Demo Repo

This repository contains two active notebooks:
- `gemini_demo_tests.ipynb`
- `outlines_demo_tests.ipynb`

## Active structure

- `common/annual_report_schema.py`
  Shared business schema for the lightweight annual report extraction flow.
- `providers/gemini/`
  Gemini PDF extraction functions and the dedicated PDF schema.
- `providers/outlines/`
  Outlines prompts, runner, and comparison helpers for the annual report extraction demos.
- `Annual_report.pdf`
  PDF used by the notebook examples.
- `legacy/`
  Archived notebooks and earlier experiments kept for reference.

## Notebooks

### `gemini_demo_tests.ipynb`
1. imports
2. simple Gemini extraction example
3. Gemini retry example

### `outlines_demo_tests.ipynb`
1. setup
2. usage examples
3. practical test cases
4. final summary table
5. complementary resources
