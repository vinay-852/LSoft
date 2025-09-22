from model.testcase_input import TestCaseInput, Step
from transform_testcase import get_testcase_output, print_steps_table
import asyncio

# Define test case input
test_case = TestCaseInput(
    Case="Create and display CO-PA documents",
    Steps=[
        Step(step_number="1", action="Create standard sales order/Sales agreement", tcodes="", sap_tcode_description=""),
        Step(step_number="2", action="Invoice created; accounting and controlling document created", tcodes="", sap_tcode_description=""),
        Step(step_number="3", action="PO for orders(service purchase)", tcodes="", sap_tcode_description=""),
        Step(step_number="4", action="Enter goods receipt", tcodes="", sap_tcode_description=""),
        Step(step_number="5", action="Enter invoice with higher/lower price than the goods receipt", tcodes="", sap_tcode_description=""),
        Step(step_number="6", action="Journal Entry using an account transferred in CO-PA", tcodes="", sap_tcode_description=""),
    ]
)

async def main():
	output = await get_testcase_output(test_case)
	if output:
		print_steps_table(output.get("Steps", []))
	else:
		print("No output generated.")

if __name__ == "__main__":
	asyncio.run(main())
