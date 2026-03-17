from numbers import Number
from typing import Any, Dict

import pandas as pd



def flatten_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    flattened = {}
    for key, value in data.items():
        dotted_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, dotted_key))
        else:
            flattened[dotted_key] = value
    return flattened



def _is_number(value: Any) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)



def values_match(expected: Any, actual: Any, tolerance: float = 1e-6) -> bool:
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False
    if _is_number(expected) and _is_number(actual):
        return abs(float(expected) - float(actual)) <= tolerance
    return expected == actual



def build_field_comparison_table(
    expected: Dict[str, Any],
    actual: Dict[str, Any] | None,
) -> pd.DataFrame:
    expected_flat = flatten_dict(expected)
    actual_flat = flatten_dict(actual or {})
    rows = []

    for field, expected_value in expected_flat.items():
        actual_value = actual_flat.get(field)
        match = values_match(expected_value, actual_value)
        rows.append(
            {
                "field": field,
                "expected": expected_value,
                "actual": actual_value,
                "result": "OK" if match else "KO",
                "match": match,
            }
        )

    return pd.DataFrame(rows, columns=["field", "expected", "actual", "result", "match"])



def style_field_comparison_table(dataframe: pd.DataFrame):
    visible_df = dataframe[["field", "expected", "actual", "result"]]

    def row_style(row):
        if row["result"] == "OK":
            color = "#e8f5e9"
            text = "#1b5e20"
        else:
            color = "#ffebee"
            text = "#b71c1c"
        return [f"background-color: {color}; color: {text}" for _ in row.index]

    return visible_df.style.apply(row_style, axis=1)



def summarize_mismatches(dataframe: pd.DataFrame, limit: int = 4) -> str:
    mismatches = dataframe.loc[~dataframe["match"], "field"].tolist()
    if not mismatches:
        return "No mismatches"
    preview = ", ".join(mismatches[:limit])
    if len(mismatches) > limit:
        preview += ", ..."
    return preview



def build_summary_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "scenario": result["scenario"],
                "expected_behavior": result["expected_problem"],
                "matched_fields": result["matched_fields"],
                "total_fields": result["total_fields"],
                "match_rate": result["match_rate"],
                "main_differences": result["main_differences"],
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "scenario",
            "expected_behavior",
            "matched_fields",
            "total_fields",
            "match_rate",
            "main_differences",
        ],
    )



def style_summary_table(dataframe: pd.DataFrame):
    def rate_style(value):
        if float(value) == 1.0:
            return "background-color: #e8f5e9; color: #1b5e20"
        return "background-color: #ffebee; color: #b71c1c"

    return dataframe.style.map(rate_style, subset=["match_rate"])

