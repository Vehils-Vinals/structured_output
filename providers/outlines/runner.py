import json
from typing import Any

import outlines as outlines_lib
from pydantic import BaseModel

from common.annual_report_schema import AnnualReportExtraction

from .comparison import build_field_comparison_table, summarize_mismatches
from .prompts import BASELINE_EXPECTED_OUTPUT, MODEL_NAME


def load_model(model_name: str = MODEL_NAME):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    hf_model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    hf_tokenizer = AutoTokenizer.from_pretrained(model_name)

    if hasattr(outlines_lib, "from_transformers"):
        return outlines_lib.from_transformers(hf_model, hf_tokenizer)

    if hasattr(outlines_lib, "models") and hasattr(outlines_lib.models, "transformers"):
        return outlines_lib.models.transformers(hf_model, hf_tokenizer)

    raise RuntimeError("Unsupported Outlines installation: no transformers adapter found.")


def extract_pdf_context(pdf_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        normalized_text = " ".join(text.lower().split())
        pages.append(
            {
                "page_number": page_number,
                "text": text,
                "normalized_text": normalized_text,
            }
        )

    if not pages:
        raise ValueError(f"No extractable text found in {pdf_path}.")

    keywords = [
        "financial results",
        "period ended",
        "revenue",
        "net income",
        "total assets",
        "total equity",
        "audit",
        "auditor",
        "opinion",
    ]

    scored_pages = []
    for page in pages:
        score = sum(1 for keyword in keywords if keyword in page["normalized_text"])
        scored_pages.append((score, page))

    scored_pages.sort(key=lambda item: (-item[0], item[1]["page_number"]))
    selected = [item[1] for item in scored_pages[:6] if item[0] > 0]
    if not selected:
        selected = pages[:6]

    selected = sorted(selected, key=lambda item: item["page_number"])
    return "\n\n".join(
        f"[[PAGE {item['page_number']}]]\n{item['text']}"
        for item in selected
    )


def run_plain_prompt(model, prompt: str, max_new_tokens: int = 512, **kwargs):
    try:
        return model(prompt, str, max_new_tokens=max_new_tokens, **kwargs)
    except TypeError:
        return model(prompt, max_new_tokens=max_new_tokens, **kwargs)


def _to_raw_output(value: Any) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, default=str)


def _extract_actual_output(value: Any) -> dict[str, Any] | None:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            candidate = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(candidate, dict):
            return candidate
    return None


def run_structured_extraction(model, prompt: str, max_new_tokens: int = 1024, **kwargs):
    try:
        raw_generation = model(
            prompt,
            AnnualReportExtraction,
            max_new_tokens=max_new_tokens,
            **kwargs,
        )
    except Exception as exc:
        return {
            "raw_output": f"<generation error>\n{exc}",
            "actual_output": None,
        }

    return {
        "raw_output": _to_raw_output(raw_generation),
        "actual_output": _extract_actual_output(raw_generation),
    }


def run_outlines_json(model, prompt: str, schema=None, max_new_tokens: int = 1024, **kwargs):
    return run_structured_extraction(
        model=model,
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        **kwargs,
    )


def run_test_case(model, case: dict[str, Any], max_new_tokens: int = 2048) -> dict[str, Any]:
    extraction = run_outlines_json(
        model=model,
        prompt=case["prompt"],
        max_new_tokens=max_new_tokens,
    )
    comparison_table = build_field_comparison_table(
        BASELINE_EXPECTED_OUTPUT,
        extraction["actual_output"],
    )
    matched_fields = int(comparison_table["match"].sum())
    total_fields = len(comparison_table.index)
    match_rate = round(matched_fields / total_fields, 3) if total_fields else 0.0

    return {
        "scenario": case["name"],
        "description": case["description"],
        "expected_problem": case["expected_problem"],
        "prompt": case["prompt"],
        "raw_output": extraction["raw_output"],
        "actual_output": extraction["actual_output"],
        "comparison_table": comparison_table,
        "matched_fields": matched_fields,
        "total_fields": total_fields,
        "match_rate": match_rate,
        "main_differences": summarize_mismatches(comparison_table),
    }
