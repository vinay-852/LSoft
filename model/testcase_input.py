from typing import List, Optional
from pydantic import BaseModel

class Step(BaseModel):
	step_number: str
	action: str
	tcodes: Optional[str]
	sap_tcode_description: Optional[str]
class TestCaseInput(BaseModel):
	Case: str
	Steps: List[Step]
