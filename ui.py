import streamlit as st
from load_data import parse_testcase_file
from convert_output import save_testcase_outputs_to_csv
from model.testcase_output import TestCaseOutput, Step as OutputStep
from model.testcase_input import TestCaseInput, Step as InputStep
from transform_testcase import get_testcase_output
import asyncio
import tempfile
import os
import random

# -----------------------------
# Async batch processing function
# -----------------------------
async def convert_input_to_output_with_transform(testcase_inputs):
    async def call_with_retry(tc, max_retries=3, base_delay=1.0):
        for attempt in range(max_retries):
            try:
                return await get_testcase_output(tc)
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                else:
                    return None

    output_map = {}
    # Process in batches of 2
    for i in range(0, len(testcase_inputs), 2):
        batch = testcase_inputs[i:i + 2]
        results = await asyncio.gather(*(call_with_retry(tc) for tc in batch))
        for idx, (tc, data) in enumerate(zip(batch, results)):
            if data:
                steps = [
                    OutputStep(
                        step_number=s.get('step_number', ''),
                        action=s.get('action', ''),
                        tcodes=s.get('tcodes', ''),
                        sap_tcode_description=s.get('sap_tcode_description', ''),
                        mandatory_fields=s.get('mandatory_fields', []),
                        output_fields=s.get('output_fields', [])
                    )
                    for s in data.get('Steps', [])
                ]
                output_map[i + idx] = TestCaseOutput(Case=data.get('Case', tc.Case), Steps=steps)

    outputs = [output_map[i] for i in range(len(testcase_inputs)) if i in output_map]
    return outputs

# -----------------------------
# Streamlit App
# -----------------------------
def main():
    st.title("Test Case Converter")
    st.write("Upload a CSV or Excel file to convert test case input to output.")

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])
    if uploaded_file:
        # Save uploaded file temporarily
        suffix = os.path.splitext(uploaded_file.name)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            testcase_inputs = parse_testcase_file(tmp_path)
            st.success(f"Parsed {len(testcase_inputs)} test cases.")

            if "processing" not in st.session_state:
                st.session_state.processing = False
            if "progress" not in st.session_state:
                st.session_state.progress = 0.0

            async def process_and_download_async():
                st.session_state.processing = True
                progress_bar = st.progress(0)
                total = len(testcase_inputs)
                batch_size = 2
                outputs = []

                for i in range(0, total, batch_size):
                    batch = testcase_inputs[i:i + batch_size]
                    batch_outputs = await convert_input_to_output_with_transform(batch)
                    outputs.extend(batch_outputs)
                    st.session_state.progress = min((i + batch_size) / total, 1.0)
                    progress_bar.progress(st.session_state.progress)

                # Save output CSV
                out_path = tmp_path + "_output.csv"
                save_testcase_outputs_to_csv(outputs, out_path)
                with open(out_path, "rb") as f:
                    st.download_button("Download Output CSV", f, file_name="testcase_output.csv")
                os.remove(out_path)
                st.session_state.processing = False
                st.session_state.progress = 0.0

            if st.button("Transform and Download Output CSV", disabled=st.session_state.processing):
                asyncio.run(process_and_download_async())

            if st.session_state.processing:
                st.info("Processing... Please wait.")
                st.progress(st.session_state.progress)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    main()
