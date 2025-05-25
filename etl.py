import pandas as pd
import sqlite3
import csv
import os

# DEMO

mimic3_dataset = "db/mimic3_demo/mimic-iii-clinical-database-demo-1.4"
output_path = "db/prepared_csv"
patient_names = "db/mimic3_demo/id2name.csv"
db_path = "db/database.db"
ext = ".csv.gz"

# FULL
mimic3_dataset = "db/mimic3_full"
output_path = "db/prepared_full_csv"
patient_names = "db/mimic3_demo/id2name.csv"
db_path = "db/database_full.db"
ext = ".csv.gz"

os.makedirs(output_path, exist_ok=True)


def read_mimic(what, ext=ext):
    data = pd.read_csv(os.path.join(mimic3_dataset, f"{what}{ext}"), low_memory=False)
    data.columns = [c.lower() for c in data.columns]
    return data


def process_names():
    data = pd.read_csv(patient_names, header=None, names=["id", "patient_name"])
    patient_dict = data.set_index("id")["patient_name"].to_dict()
    return patient_dict


def process_demographic():
    demographic_output_path = os.path.join(output_path, "demographic.csv")
    admissions_df = read_mimic("ADMISSIONS")
    patients_df = read_mimic("PATIENTS")

    names = process_names()
    merged_df = pd.merge(admissions_df, patients_df, on="subject_id")

    merged_df["name"] = merged_df["subject_id"].map(names)
    merged_df["age"] = (
        pd.to_datetime(merged_df["admittime"]).dt.year
        - pd.to_datetime(merged_df["dob"]).dt.year
    )
    merged_df.loc[merged_df["age"] > 89, "age"] = merged_df["age"] - 300 + 89
    merged_df["days_of_hospital_stay"] = (
        pd.to_datetime(merged_df["dischtime"]) - pd.to_datetime(merged_df["admittime"])
    ).dt.days
    merged_df["dob_year"] = pd.to_datetime(merged_df["dob"]).dt.year
    merged_df["dod_year"] = pd.to_datetime(merged_df["dod"]).dt.year
    merged_df["admission_year"] = pd.to_datetime(merged_df["admittime"]).dt.year

    merged_df["age"] = merged_df["age"].astype(int)
    merged_df["dob_year"] = merged_df["dob_year"].astype(int)
    merged_df["dod_year"] = merged_df["dod_year"].fillna(0).astype(int)

    header_mapping = {
        "subject_id": "SUBJECT_ID",
        "hadm_id": "HADM_ID",
        "name": "NAME",
        "marital_status": "MARITAL_STATUS",
        "age": "AGE",
        "dob": "DOB",
        "gender": "GENDER",
        "language": "LANGUAGE",
        "religion": "RELIGION",
        "admission_type": "ADMISSION_TYPE",
        "days_of_hospital_stay": "DAYS_STAY",
        "insurance": "INSURANCE",
        "ethnicity": "ETHNICITY",
        "hospital_expire_flag": "EXPIRE_FLAG",
        "admission_location": "ADMISSION_LOCATION",
        "discharge_location": "DISCHARGE_LOCATION",
        "diagnosis": "DIAGNOSIS",
        "dod": "DOD",
        "dob_year": "DOB_YEAR",
        "dod_year": "DOD_YEAR",
        "admittime": "ADMITTIME",
        "dischtime": "DISCHTIME",
        "admission_year": "ADMITYEAR",
    }

    header = list(header_mapping.values())
    demographic_df = merged_df.rename(columns=header_mapping)[header]

    demographic_df.to_csv(
        demographic_output_path, index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    print(f"Demographic data has been saved to {demographic_output_path}.")

    subject_ids = set(demographic_df["SUBJECT_ID"].values.tolist())
    print(f"There were {len(subject_ids)} patients.")


def process_diagnoses():
    diagnoses_output_path = os.path.join(output_path, "diagnoses.csv")

    left = read_mimic("DIAGNOSES_ICD")
    right = read_mimic("D_ICD_DIAGNOSES")

    left = left.drop(columns=["row_id", "seq_num"])
    right = right.drop(columns=["row_id"])

    merged = pd.merge(left, right, on="icd9_code")
    merged = merged.sort_values(by="hadm_id")

    merged.columns = [col.upper() for col in merged.columns]

    merged.to_csv(
        diagnoses_output_path, sep=",", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    print(f"Diagnoses data has been saved to {diagnoses_output_path}.")


def process_procedures():
    procedures_output_path = os.path.join(output_path, "procedures.csv")

    left = read_mimic("PROCEDURES_ICD")
    right = read_mimic("D_ICD_PROCEDURES")

    left = left.drop(columns=["row_id", "seq_num"])
    right = right.drop(columns=["row_id"])

    merged = pd.merge(left, right, on="icd9_code")
    merged = merged.sort_values(by="hadm_id")

    merged.columns = [col.upper() for col in merged.columns]

    merged.to_csv(
        procedures_output_path, sep=",", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    print(f"Procedures data has been saved to {procedures_output_path}.")


def process_prescriptions():
    prescriptions_output_path = os.path.join(output_path, "prescriptions.csv")

    data = read_mimic("PRESCRIPTIONS")
    data = data.drop(
        columns=[
            "row_id",
            "gsn",
            "drug_name_poe",
            "drug_name_generic",
            "ndc",
            "prod_strength",
            "form_val_disp",
            "form_unit_disp",
            "startdate",
            "enddate",
        ]
    )
    data = data.dropna(subset=["dose_val_rx", "dose_unit_rx"])
    data["drug_dose"] = data[["dose_val_rx", "dose_unit_rx"]].apply(
        lambda x: "".join(x), axis=1
    )
    data = data.drop(columns=["dose_val_rx", "dose_unit_rx"])

    data.columns = [col.upper() for col in data.columns]

    data.to_csv(
        prescriptions_output_path, sep=",", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    print(f"Prescriptions data has been saved to {prescriptions_output_path}.")


def process_lab():
    lab_output_path = os.path.join(output_path, "lab.csv")

    labevents_df = read_mimic("LABEVENTS")
    d_labitems_df = read_mimic("D_LABITEMS")

    labevents_df = labevents_df.dropna(subset=["hadm_id", "value", "valueuom"])
    labevents_df = labevents_df.drop(columns=["row_id", "valuenum"])
    labevents_df["value_unit"] = labevents_df[["value", "valueuom"]].apply(
        lambda x: "".join(x), axis=1
    )
    labevents_df = labevents_df.drop(columns=["value", "valueuom"])

    d_labitems_df = d_labitems_df.drop(columns=["row_id", "loinc_code"])

    merged_df = pd.merge(labevents_df, d_labitems_df, on="itemid")

    merged_df.columns = [col.upper() for col in merged_df.columns]

    merged_df.to_csv(
        lab_output_path, sep=",", index=False, quoting=csv.QUOTE_NONNUMERIC
    )
    print(f"Lab data has been saved to {lab_output_path}.")


def recreate_db():

    csv_files = [
        "demographic",
        "diagnoses",
        "lab",
        "prescriptions",
        "procedures",
    ]

    conn = sqlite3.connect(db_path)

    for _, csv_file in enumerate(csv_files, start=1):
        table_name = csv_file

        df = pd.read_csv(os.path.join(output_path, csv_file + ".csv"))
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    for table in csv_files:
        query = f"""
        SELECT count(1) 
        FROM {table} 
        """

        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        print(f"Inserted {results[0][0]} in {table}.")

    conn.close()


if __name__ == "__main__":
    # subject_ids = process_demographic()
    # process_diagnoses()
    # process_procedures()
    # process_prescriptions()
    process_lab()

    recreate_db()

"""
CREATE INDEX "idx_demographic_hadm_id" ON "demographic" ( "HADM_ID" );
CREATE INDEX "idx_diagnoses_hadm_id" ON "diagnoses" ( "HADM_ID" );
CREATE INDEX "idx_lab_hadm_id" ON "lab" ( "HADM_ID" );
CREATE INDEX "idx_procedures_hadm_id" ON "procedures" ( "HADM_ID" );
CREATE INDEX "idx_prescriptions_hadm_id" ON "prescriptions" ( "HADM_ID" );

CREATE INDEX "idx_demographic_subject_id" ON "demographic" ( "SUBJECT_ID" );
CREATE INDEX "idx_diagnoses_subject_id" ON "diagnoses" ( "SUBJECT_ID" );
CREATE INDEX "idx_lab_subject_id" ON "lab" ( "SUBJECT_ID" );
CREATE INDEX "idx_procedures_subject_id" ON "procedures" ( "SUBJECT_ID" );
CREATE INDEX "idx_prescriptions_subject_id" ON "prescriptions" ( "HADM_ID" );

"""
