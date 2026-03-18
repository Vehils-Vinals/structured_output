# Structured Output Demo Repo

This project demonstrates two practical ways to generate structured data from documents and text:

- **Outlines** for local schema-guided structured generation
- **Gemini** for PDF extraction with schema-constrained JSON output

The goal is not only to show the final result, but to make it easy to understand **how each approach works**, **where the implementation lives**, and **how to run the demos yourself**.

## What This Repository Demonstrates

The repository contains two educational demo flows:

- **Outlines demo**
  This flow shows how to guide a local language model toward a structured extraction target, compare the generated result with an expected reference output, and summarize the differences in a readable way.
- **Gemini demo**
  This flow shows how to send a PDF to Gemini, request JSON constrained by a schema, and run a retry loop when the first structured answer is not usable.

Both demos are meant to be read as implementation examples, not only as notebooks to execute.

## Where The Implementation Lives

### Shared extraction schema

- [structured_output/common/annual_report_schema.py](common/annual_report_schema.py)
  Shared `AnnualReportExtraction` schema used by the lightweight annual-report extraction flow.

### Outlines implementation

- [structured_output/providers/outlines/prompts.py](providers/outlines/prompts.py)
  Prompt builders, baseline text fixture, expected output, practical test cases, and complementary resources.
- [structured_output/providers/outlines/runner.py](providers/outlines/runner.py)
  Model loading, prompt execution, guided structured generation, and scenario execution helpers.
- [structured_output/providers/outlines/comparison.py](providers/outlines/comparison.py)
  Field-by-field comparison logic, mismatch summaries, and styled recap tables.
- [structured_output/outlines_demo_tests.ipynb](outlines_demo_tests.ipynb)
  Notebook that demonstrates the Outlines flow in practice.

### Gemini implementation

- [structured_output/providers/gemini/runner.py](providers/gemini/runner.py)
  Simple Gemini extraction and retry-based Gemini extraction.
- [structured_output/providers/gemini/schemas_for_pdf.py](providers/gemini/schemas_for_pdf.py)
  Dedicated PDF extraction schema used by Gemini.
- [structured_output/gemini_demo_tests.ipynb](gemini_demo_tests.ipynb)
  Notebook that demonstrates the Gemini PDF extraction flow.

### Source document

- [structured_output/Annual_report.pdf](Annual_report.pdf)
  PDF used by the demo notebooks.

## How Outlines Works

The Outlines flow is organized around a small annual-report extraction task.

1. A prompt is built from a controlled annual-report text excerpt.
   Implementation: [structured_output/providers/outlines/prompts.py](providers/outlines/prompts.py)
2. A local model is loaded with `load_model(...)`.
   Implementation: [structured_output/providers/outlines/runner.py](providers/outlines/runner.py)
3. A free-form prompt can be run with `run_plain_prompt(...)` to see an unconstrained answer.
   Implementation: [structured_output/providers/outlines/runner.py](providers/outlines/runner.py)
4. A schema-guided extraction is run with `run_outlines_json(...)`, which pushes the generation toward `AnnualReportExtraction`.
   Implementation: [structured_output/providers/outlines/runner.py](providers/outlines/runner.py)
5. The generated structure is compared field by field against the expected extraction using `build_field_comparison_table(...)`.
   Implementation: [structured_output/providers/outlines/comparison.py](providers/outlines/comparison.py)
6. Practical scenarios are executed with `run_test_case(...)`, then summarized in a final recap table.
   Implementation: [structured_output/providers/outlines/runner.py](providers/outlines/runner.py), [structured_output/providers/outlines/comparison.py](providers/outlines/comparison.py)

The main notebook for this flow is [structured_output/outlines_demo_tests.ipynb](outlines_demo_tests.ipynb).

### Outlines APIs used in the README demo

- `load_model(...)`
- `run_plain_prompt(...)`
- `run_outlines_json(...)`
- `run_test_case(...)`

## How Gemini Works

The Gemini flow is focused on structured extraction from a PDF.

1. The prompt is defined directly in the notebook example.
   Implementation: [structured_output/gemini_demo_tests.ipynb](gemini_demo_tests.ipynb)
2. The PDF is uploaded to Gemini inside `process_annual_report_gemini(...)` or `process_annual_report_with_retry(...)`.
   Implementation: [structured_output/providers/gemini/runner.py](providers/gemini/runner.py)
3. Gemini is asked to produce JSON constrained by `response_schema=AnnualReportExtraction`.
   Implementation: [structured_output/providers/gemini/runner.py](providers/gemini/runner.py)
4. The schema used for this PDF extraction is the dedicated Gemini schema in `providers/gemini/schemas_for_pdf.py`.
   Implementation: [structured_output/providers/gemini/schemas_for_pdf.py](providers/gemini/schemas_for_pdf.py)
5. The retry path re-runs the request when JSON parsing or local validation fails.
   Implementation: [structured_output/providers/gemini/runner.py](providers/gemini/runner.py)

The main notebook for this flow is [structured_output/gemini_demo_tests.ipynb](gemini_demo_tests.ipynb).

### Gemini APIs used in the README demo

- `process_annual_report_gemini(...)`
- `process_annual_report_with_retry(...)`

## How To Run The Demos

### Outlines notebook

Open [structured_output/outlines_demo_tests.ipynb](outlines_demo_tests.ipynb) and run the cells in order.

Expected flow:

1. install dependencies if needed
2. load the local model
3. run the free-form JSON example
4. run the Outlines-guided extraction example
5. run the practical test cases
6. inspect the final summary table

### Gemini notebook

Open [structured_output/gemini_demo_tests.ipynb](gemini_demo_tests.ipynb) and run the cells in order.

Before execution:

1. set `api_key = ""` to your real Gemini API key
2. keep `path_to_pdf = "Annual_report.pdf"` unless you want to test another document

Expected flow:

1. run the simple Gemini extraction example
2. run the retry-based Gemini extraction example
3. inspect the JSON returned by each call

### Important note about notebook outputs on GitHub

Notebook outputs appear on GitHub only if they are saved inside the `.ipynb` file before the file is committed and pushed.

## Repo Map

### Active entrypoints

- [structured_output/gemini_demo_tests.ipynb](gemini_demo_tests.ipynb)
- [structured_output/outlines_demo_tests.ipynb](outlines_demo_tests.ipynb)

### Active packages

- [structured_output/providers/gemini](providers/gemini)
- [structured_output/providers/outlines](providers/outlines)
- [structured_output/common](common)

### Archive

- [structured_output/legacy](legacy)

This folder contains archived notebooks and reference material. It is secondary to the active notebooks and provider packages above.
