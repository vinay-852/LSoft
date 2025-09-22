import asyncio
import json
import logging
from tabulate import tabulate

from config.ai_client import AIclient
from model.testcase_input import TestCaseInput, Step

client = AIclient()

def build_prompt(test_case):
    return f"""
You are provided with an SAP test case object that contains the following fields:
- Case
- Steps (each step includes: step_number, action, tcodes, sap_tcode_description)

Your task is to transform this input into a structured JSON object that conforms exactly to the schema below:

### Output Schema
{{
  "Case": "string",
  "Steps": [
    {{
      "step_number": "string (sequential index starting from 1)",
      "action": "string (short descriptive action)",
      "tcodes": "string (validated SAP transaction code, or 'none')",
      "sap_tcode_description": "string (short explanation of the tcode)",
      "mandatory_fields": ["list", "of", "key", "fields"],
      "output_fields": ["list", "of", "resulting", "fields"]
    }}
  ]
}}

### Transformation Rules
1. Validate tcodes and descriptions.
2. Populate mandatory_fields and output_fields.
3. Output valid JSON only.

### Input
{{
  "Case": "{test_case.Case}",
  "Steps": {json.dumps([step.model_dump() for step in test_case.Steps], indent=2)}
}}
"""

def _sync_get_testcase_output(test_case):
    """Synchronous Gemini call wrapped for async usage."""
    prompt = build_prompt(test_case)
    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        data = json.loads(content)

        # Merge missing fields
        if isinstance(data, dict):
            data.setdefault("Case", getattr(test_case, "Case", ""))
            if "Steps" in data and hasattr(test_case, "Steps"):
                for idx, input_step in enumerate(test_case.Steps):
                    if idx < len(data["Steps"]):
                        output_step = data["Steps"][idx]
                        for field in ("step_number", "action", "tcodes", "sap_tcode_description"):
                            output_step.setdefault(field, getattr(input_step, field, ""))
        return data
    except Exception as e:
        logging.error("Error parsing LLM response: %s", str(e))
        return None

async def get_testcase_output(test_case):
    """Async wrapper around the blocking Gemini call."""
    return await asyncio.to_thread(_sync_get_testcase_output, test_case)

def print_steps_table(steps):
    if steps:
        headers = ["step_number", "action", "tcodes", "sap_tcode_description", "mandatory_fields", "output_fields"]
        table = []
        for step in steps:
            table.append([
                step.get("step_number", ""),
                step.get("action", ""),
                step.get("tcodes", ""),
                step.get("sap_tcode_description", ""),
                ", ".join(step.get("mandatory_fields", [])),
                ", ".join(step.get("output_fields", []))
            ])
        print(tabulate(table, headers=headers, tablefmt="grid"))
    else:
        print("No steps found in response.")