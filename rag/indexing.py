import os
import re
import rag.parser
import rag.search

folder_name = "dataset/synthetic_patients_v2_100"

patients = []
for file_path in os.listdir(folder_name):
    m = re.fullmatch(r"patient_(\d+)\.md", file_path)
    if m:
        patient_id = int(m.group(1))
        full_path = os.path.join(folder_name, file_path)

        with open(full_path, "r") as f:
            contents = f.read()

        sections = rag.parser.get_sections(contents)

        patients.append(
            {
                "patient_id": patient_id,
                "sections": sections,
            }
        )

rag.search.index_patients(patients)
