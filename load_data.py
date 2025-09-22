import pandas as pd
from model.testcase_input import TestCaseInput, Step

def parse_testcase_file(file_path: str):
	"""
	Parse a CSV or Excel file and convert rows into TestCaseInput objects.
	Expects columns: Case, Step #, Action
	"""
	testcases = []
	if file_path.endswith('.csv'):
		df = pd.read_csv(file_path)
		dfs = [df]
	else:
		dfs = pd.read_excel(file_path, sheet_name=None).values()

	for df in dfs:
		for case, group in df.groupby('Case'):
			steps = []
			for _, row in group.iterrows():
				step_number = str(row.get('Step #', '')).strip()
				action = str(row.get('Action', '')).strip()
				tcodes = str(row.get('tcodes', '')).strip() if 'tcodes' in df.columns else None
				sap_tcode_description = str(row.get('sap_tcode_description', '')).strip() if 'sap_tcode_description' in df.columns else None
				if not any([step_number, action, tcodes, sap_tcode_description]):
					continue
				if action.lower() == 'action':
					continue
				steps.append(Step(
					step_number=step_number,
					action=action,
					tcodes=tcodes,
					sap_tcode_description=sap_tcode_description
				))
			testcases.append(TestCaseInput(Case=case, Steps=steps))
	return testcases