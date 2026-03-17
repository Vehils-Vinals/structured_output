import json
from typing import Any

import outlines
from pydantic import BaseModel

from .comparison import build_field_comparison_table, summarize_mismatches
from .prompts import BASELINE_EXPECTED_OUTPUT, MODEL_NAME
from .schemas_for_test import AnnualReportExtraction



def load_model(model_name: str = MODEL_NAME):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    hf_model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    hf_tokenizer = AutoTokenizer.from_pretrained(model_name)

    if hasattr(outlines, "from_transformers"):
        return outlines.from_transformers(hf_model, hf_tokenizer)

    if hasattr(outlines, "models") and hasattr(outlines.models, "transformers"):
        return outlines.models.transformers(model_name, device="auto")

    raise RuntimeError("Unsupported Outlines installation: no transformers adapter found.")



def run_plain_prompt(model, prompt: str, max_new_tokens: int = 512, **kwargs):
    try:
        return model(prompt, str, max_new_tokens=max_new_tokens, **kwargs)
    except TypeError:
        return model(prompt, max_new_tokens=max_new_tokens, **kwargs)



def _to_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return None



def _to_raw_output(value: Any) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, default=str)



def _extract_actual_output(value: Any) -> dict[str, Any] | None:
    direct_value = _to_dict(value)
    if direct_value is not None:
        return direct_value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return _to_dict(parsed)

    return None



def run_outlines_json(model, prompt: str, schema=None, max_new_tokens: int = 1024, **kwargs):
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
