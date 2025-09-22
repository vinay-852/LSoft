from config.ai_client import AIclient
from model.testcase_input import TestCaseInput, Step
from model.testcase_output import TestCaseOutput

import asyncio
import json
from tabulate import tabulate

client = AIclient()

def build_prompt(test_case):
    """Builds the prompt for the AI model from a test_case object."""
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
1. For each step:
   - Validate and correct the "tcodes". If invalid or missing, replace with the correct one, or use "none" if unknown.
   - Expand or correct the "sap_tcode_description" to be clear and accurate.
   - Populate "mandatory_fields" with the key input fields required for the step.
   - Populate "output_fields" with the fields or results produced by the step.
   - Ensure the "action" remains concise yet descriptive.

2. Validation rules:
   - Replace wrong or missing tcodes with the correct value or "none".
   - Improve incomplete tcode descriptions with logical detail.
   - Always provide non-empty "mandatory_fields" and "output_fields".

3. Output:
   - Ensure the final output is **valid JSON only** and adheres strictly to the schema.
   - Do not include any explanations, commentary, or text outside of the JSON.

### Input
{{
  "Case": "{test_case.Case}",
  "Steps": {json.dumps([step.model_dump() for step in test_case.Steps], indent=2)}
}}
"""

async def get_testcase_output(test_case):
    """Calls the AI model and returns the parsed output JSON for the given test_case object."""
    prompt = build_prompt(test_case)
    def sync_call():
        return client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )
    response = await asyncio.to_thread(sync_call)
    content = response.choices[0].message.content.strip()
    try:
        data = json.loads(content)
        return data
    except Exception as e:
        print("Error parsing response as JSON:", e)
        print("Raw content returned:\n", content)
        return None

def print_steps_table(steps):
    """Prints the steps in a tabular format."""
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
