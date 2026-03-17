import os
import json
import time
from google import genai
from google.genai import types
from pydantic import ValidationError

from .schemas_for_pdf import AnnualReportExtraction


def process_annual_report_gemini(pdf_path: str, api_key: str, prompt: str) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Target file not found: {pdf_path}")

    client = genai.Client(api_key=api_key)
    
    print(f"Uploading file to Gemini API: {pdf_path}")
    uploaded_file = client.files.upload(
        file=pdf_path, 
        config={'display_name': 'Annual_Report_Target'}
    )

    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AnnualReportExtraction,
        temperature=0.0
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt],
            config=generation_config
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        return {}
    finally:
        print(f"Deleting remote file: {uploaded_file.name}")
        client.files.delete(name=uploaded_file.name)


def process_annual_report_with_retry(pdf_path: str, api_key: str, initial_prompt: str, max_retries: int = 2) -> dict:

    # 1. Upload initial
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Target file not found: {pdf_path}")

    client = genai.Client(api_key=api_key)

    print(f"Uploading file to Gemini API: {pdf_path}")
    uploaded_file = client.files.upload(
        file=pdf_path,
        config={'display_name': 'Annual_Report_Target'}
    )

    current_prompt = initial_prompt
    attempts = 0

    while attempts <= max_retries:
        print(f"--- Attempt {attempts + 1}/{max_retries + 1} ---")

        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnnualReportExtraction,
            temperature=0.0 # Crucial pour la reproductibilité lors des retries
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash', # Version recommandée
            contents=[uploaded_file, current_prompt],
            config=generation_config
        )
        # --- INJECTION DE BUG POUR TEST ---
        #if attempts == 0:
        #    print("DEBUG: Simulation d'un JSON corrompu pour le test...")
        #    response = '{"ceci_n_est_pas_du_json": ...' # Force une JSONDecodeError
        # ----------------------------------
        try:
            # Tentative de validation Pydantic
            raw_json = json.loads(response.text)
            validated_data = AnnualReportExtraction(**raw_json)

            print("Extraction successful and validated.")
            return raw_json

        except (ValidationError, json.JSONDecodeError, Exception) as e:
            attempts += 1
            if attempts > max_retries:
                print("Nombre maximal de tentatives atteint.")
                return raw_json if 'raw_json' in locals() else {}

            # Gestion de l'erreur et préparation du retry
            error_message = str(e)
            print(f"Échec de validation ou erreur API : {error_message}")

            current_prompt = (
                f"{initial_prompt}\n\n"
                f"CORRECTION REQUISE : Ton précédent résultat a généré l'erreur suivante :\n"
                f"{error_message}\n\n"
                "Analyse à nouveau le document et corrige les données en respectant strictement le schéma."
            )

    return {}

