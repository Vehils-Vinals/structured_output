from copy import deepcopy

CANONICAL_PDF_PATH = "Annual_report.pdf"
MODEL_NAME = "HuggingFaceTB/SmolLM2-135M-Instruct"

BASELINE_REPORT_TEXT = """
Dassault Systemes SE reports its consolidated financial results for the year ended 2024-12-31.
The comparative previous period ended on 2023-12-31.

Income Statement Analysis:
Total revenue for the current period reached 6213.60, compared to 5951.40 in the previous period.
Net income stood at 1198.10, representing an increase from 1050.20 in the prior year.
All income statement figures are reported in USD and expressed in Millions.

Balance Sheet Overview:
Total assets amounted to 15545.90, up from 14622.50 at the end of the previous period.
Total equity was recorded at 9080.70, compared to 7846.10 previously.
Balance sheet figures are also reported in USD and expressed in Millions.

Audit Information:
The independent audit was conducted by PricewaterhouseCoopers Audit.
The auditor's assessment is as follows: "In our opinion, the consolidated financial statements give a true and fair view of the assets and liabilities and of the financial position of the Group."
""".strip()

REFERENCE_EXTRACTION = {
    "parent_company": "Dassault Systemes SE",
    "financial_statement_period": "2024-12-31",
    "previous_period": "2023-12-31",
    "income_statement": {
        "total_revenue": 6213.6,
        "net_income": 1198.1,
        "total_revenue_previous": 5951.4,
        "net_income_previous": 1050.2,
        "currency": "USD",
        "units": "Millions",
    },
    "balance_sheet": {
        "total_assets": 15545.9,
        "total_equity": 9080.7,
        "total_assets_previous": 14622.5,
        "total_equity_previous": 7846.1,
        "currency": "USD",
        "units": "Millions",
    },
    "audit": {
        "auditor_company": "PricewaterhouseCoopers Audit",
        "auditor_assessment": (
            "In our opinion, the consolidated financial statements give a true "
            "and fair view of the assets and liabilities and of the financial "
            "position of the Group."
        ),
    },
}

BASELINE_EXPECTED_OUTPUT = deepcopy(REFERENCE_EXTRACTION)


def _empty_extraction():
    return {
        "parent_company": None,
        "financial_statement_period": None,
        "previous_period": None,
        "income_statement": {
            "total_revenue": None,
            "net_income": None,
            "total_revenue_previous": None,
            "net_income_previous": None,
            "currency": None,
            "units": None,
        },
        "balance_sheet": {
            "total_assets": None,
            "total_equity": None,
            "total_assets_previous": None,
            "total_equity_previous": None,
            "currency": None,
            "units": None,
        },
        "audit": {
            "auditor_company": None,
            "auditor_assessment": None,
        },
    }


def build_plain_prompt(document_text: str) -> str:
    return (
        "Read the annual report excerpt below and return a JSON object with "
        "the following keys: parent_company, financial_statement_period, "
        "previous_period, income_statement, balance_sheet, and audit. "
        "The nested objects must contain all main metrics mentioned in the document.\n\n"
        f"Document:\n{document_text}"
    )


def build_outlines_prompt(document_text: str) -> str:
    return (
        "Extract all data required for the annual report extraction.\n"
        "Use only the information explicitly present in the document.\n"
        "Extract the parent company, reporting dates, income statement values, "
        "balance sheet values, and audit information.\n"
        "Do not add commentary or invent unsupported values.\n\n"
        f"Document:\n{document_text}"
    )


def build_structured_prompt(document_text: str, extra_rules: str = "") -> str:
    prompt_lines = [
        "Extract all data required for the annual report extraction.",
        "Use only information explicitly stated in the document.",
        "Return null when a field is missing or unreadable.",
        "Do not add commentary.",
    ]
    if extra_rules:
        prompt_lines.append(extra_rules)

    prompt_lines.append("")
    prompt_lines.append(f"Document:\n{document_text}")
    return "\n".join(prompt_lines)


def _copy_reference():
    return deepcopy(REFERENCE_EXTRACTION)


MISSING_AUDIT_TEXT = "\n".join(
    line
    for line in BASELINE_REPORT_TEXT.splitlines()
    if "Audit" not in line and "auditor" not in line.lower()
)
UNREADABLE_EQUITY_TEXT = BASELINE_REPORT_TEXT.replace(
    "Total equity was recorded at 9080.70",
    "Total equity was recorded at toto",
)
CONTRADICTORY_REVENUE_TEXT = (
    BASELINE_REPORT_TEXT
    + "\nCorrection note: total revenue for the current period was 9999.99 instead of 6213.60."
)

missing_audit_expected = _copy_reference()
missing_audit_expected["audit"] = {
    "auditor_company": None,
    "auditor_assessment": None,
}

unreadable_equity_expected = _copy_reference()
unreadable_equity_expected["balance_sheet"]["total_equity"] = None

contradictory_revenue_expected = _copy_reference()
contradictory_revenue_expected["income_statement"]["total_revenue"] = 9999.99

TEST_CASES = [
    {
        "name": "baseline_financial_report",
        "description": "Rapport coherent avec toutes les valeurs attendues.",
        "expected_problem": "Le modele doit retrouver exactement les donnees du rapport de reference.",
        "prompt": build_structured_prompt(BASELINE_REPORT_TEXT),
        "expected_output": _copy_reference(),
    },
    {
        "name": "incoherent_prompt",
        "description": "Prompt hors sujet sans rapport financier.",
        "expected_problem": "Le modele ne doit pas produire une extraction valide credible a partir d'un prompt hors sujet.",
        "prompt": "Write a poem about clouds.",
        "expected_output": _empty_extraction(),
    },
    {
        "name": "non_financial_input",
        "description": "Description non financiere d'une scene.",
        "expected_problem": "Le modele ne doit pas inventer un rapport annuel a partir d'une simple description d'image.",
        "prompt": build_structured_prompt(
            "Image description: Donald Duck is smiling in front of a castle."
        ),
        "expected_output": _empty_extraction(),
    },
    {
        "name": "unreadable_required_field",
        "description": "Champ requis illisible dans le bilan.",
        "expected_problem": "Le modele ne doit pas valider proprement une extraction si une valeur cle du bilan est illisible.",
        "prompt": build_structured_prompt(UNREADABLE_EQUITY_TEXT),
        "expected_output": unreadable_equity_expected,
    },
    {
        "name": "missing_audit_section",
        "description": "Section audit absente du document.",
        "expected_problem": "Le modele ne doit pas inventer les informations d'audit manquantes.",
        "prompt": build_structured_prompt(MISSING_AUDIT_TEXT),
        "expected_output": missing_audit_expected,
    },
    {
        "name": "contradictory_revenue_values",
        "description": "Presence d'une note corrective contradictoire.",
        "expected_problem": "Le modele doit tenir compte de la note corrective et privilegier la valeur corrigee du chiffre d'affaires.",
        "prompt": build_structured_prompt(
            CONTRADICTORY_REVENUE_TEXT,
            "If the document provides a correction note for a metric, use the corrected value for that metric.",
        ),
        "expected_output": contradictory_revenue_expected,
    },
]

APPENDIX_ITEMS = [
    {
        "resource": "Annual_report.pdf",
        "role": "Document source utilise par les demonstrations du repo.",
    },
    {
        "resource": "common/annual_report_schema.py",
        "role": "Schema partage pour l''extraction structuree du rapport annuel.",
    },
    {
        "resource": "providers/outlines/",
        "role": "Prompts, runner et comparaisons utilises par ce notebook.",
    },
]
