from typing import List
from pydantic import BaseModel

class Step(BaseModel):
	step_number: str
	action: str
	tcodes: str
	sap_tcode_description: str
	mandatory_fields: List[str]
	output_fields: List[str]
class TestCaseOutput(BaseModel):
	Case: str
	Steps: List[Step]
	


