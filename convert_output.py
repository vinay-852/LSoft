import pandas as pd
from model.testcase_output import TestCaseOutput, Step
from typing import List

def save_testcase_outputs_to_csv(testcase_outputs: List[TestCaseOutput], file_path: str):
    """
    Save all TestCaseOutput objects to a single CSV file in the given order.
    Each step will be a row, with columns for Case, Step #, Action, tcodes, sap_tcode_description, mandatory_fields, output_fields.
    """
    rows = []
    for testcase in testcase_outputs:
        for step in testcase.Steps:
            rows.append({
                'Test Case Name': testcase.Case,
                'Step': step.step_number,
                'Action': step.action,
                'Tcodes': step.tcodes,
                'SAP Tcode Description': step.sap_tcode_description,
                'Mandatory Fields': ', '.join(step.mandatory_fields) if step.mandatory_fields else '',
                'Output Fields': ', '.join(step.output_fields) if step.output_fields else ''
            })
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False)
