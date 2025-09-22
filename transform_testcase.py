import asyncio
import json
import logging
from tabulate import tabulate

from config.ai_client import AIclient
from model.testcase_input import TestCaseInput, Step

client = AIclient()

def build_prompt(test_case):
        test_case_json = json.dumps({
                "Case": getattr(test_case, "Case", ""),
                "Steps": [step.model_dump() for step in getattr(test_case, "Steps", [])]
        }, indent=2)
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

### Enhanced Transformation Rules

1. **Transaction Code Validation**
   - If `tcodes` are provided, verify them against known SAP transaction codes.
   - Confirm that each `tcode` aligns with the described business action or process.
   - Flag mismatches between `tcode` functionality and description.

2. **Missing Transaction Codes**
   - If `tcode` is missing but an action description is present, attempt to infer the most likely `tcode`.
   - Use domain knowledge and context clues from the description to map to SAP transactions.
   - If inference is not possible, assign `"none"`.

3. **Field Completion**
   - Fill in all missing fields where possible:
     - Derive from the action description.
     - Infer from common SAP business processes.
     - Use defaults if no clear match exists.

4. **Fallback Rules**
   - If no suitable `tcode` exists or functionality cannot be determined, always return `"none"`.
   - Do not invent or create custom `tcodes`.

5. **Output Fields**
   - Always provide `output_fields` that specify what data or artifacts result from executing the action.
   - If unknown, return `"none"`.



### Input
{test_case_json}
"""

def _sync_get_testcase_output(test_case):
    """Synchronous Gemini call wrapped for async usage."""
    prompt = build_prompt(test_case)
    try:
        print(prompt)
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