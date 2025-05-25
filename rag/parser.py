import re


def split_markdown_by_subchapters(text, level=2, min_lines=2):
    pattern = "#" * level
    pattern = rf"(^{pattern}\s+.*$)"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    sections = []
    current_section = ""

    def potentialy_add(current_section):
        if current_section and len(current_section.strip().split("\n")) >= min_lines:
            sections.append(current_section.strip())

    for part in parts:
        if part.startswith("##"):
            potentialy_add(current_section)
            current_section = part
        else:
            current_section += "\n" + part

    potentialy_add(current_section)

    return sections


def get_sections(text):
    sections = split_markdown_by_subchapters(text, level=2)
    final_sections = []
    for s in sections:
        title = s.split("\n")[0]
        if len(s) > 1000:
            subsections = split_markdown_by_subchapters(s, level=3)
            for i, s in enumerate(subsections):
                if i > 0:
                    s = title + "\n" + s
                final_sections.append(s)
            continue
        final_sections.append(s)

    return final_sections


text = """
# Patient Record (ID: 45)

# Patient Record

## Patient Information

- **Patient ID:** 00001
- **Name:** Jane Doe
- **Age:** 40 years
- **Gender:** Female
- **Marital Status:** Divorced
- **Occupation:** Nurse
- **Registration Date:** April 1, 2024
- **Attending Physician:** Dr. Emily Smith, Gynecologic Specialist
- **Referred By:** Primary Care Physician
- **Insurance:** HealthSecure
  - **Policy Number:** 7688536864
  - **Coverage:** Full coverage for diagnostics, imaging, and hospitalization
  - **Annual Deductible:** $1,000
  - **Co-Payments:** Apply for specialist visits
  - **Prior Authorization:** Obtained for pelvic MRI and further testing
- **Emergency Contacts:**
  - **Primary:** Contact 1, Phone: (555) 472-6833, Email: contact1@example.com
  - **Secondary:** Contact 2 (Sister), Phone: (555) 987-6543
- **Billing Address:** 222 Elm Street, San Diego, USA
- **Outstanding Balance:** None
- **HIPAA Authorization:** Signed for emergency contacts

## Medical Patient Record

### Chief Complaint
Jane Doe is experiencing chronic pelvic pain that has worsened over the past 12 months. She describes it as a dull ache in the lower abdomen, which sometimes becomes sharp during menstruation. She has also noticed an increase in menstrual flow duration, lasting up to 10 days, accompanied by fatigue, bloating, and nausea.

### History of Present Illness
Her symptoms began approximately a year ago with irregular menstrual cycles and progressively heavier bleeding. The pain is localized to the lower abdominal region, worsens with physical activity, and is sometimes severe enough to interfere with work. She reports occasional dizziness and increased urinary frequency during menstruation.

### Past Medical History
- **Anemia:** Likely due to blood loss from heavy menstrual cycles
- **Hypertension:** Diagnosed at age 35, managed with Losartan 50 mg daily
- **Previous Surgeries:** Appendectomy at age 18 and two cesarean sections
- **Family History:** 
  - Mother had uterine fibroids, treated surgically at age 45
  - Sister has endometriosis
  - Father has hypertension and diabetes

### Gynecological History
- **Menarche:** Age 12
- **Irregular Periods:** Since adolescence, previously lasting 5-6 days, now 7-10 days with increased clotting
- **Obstetric History:** G2P2 with two full-term pregnancies
- **Contraceptives:** Used for 15 years, discontinued at age 35
- **Pap Smear:** Last normal 18 months ago
- **Uterine Fibroids:** Diagnosed at age 38, previously asymptomatic

### Social History
- **Smoking:** Never
- **Alcohol:** Occasionally (1-2 glasses of wine per month)
- **Physical Activity:** Daily 20-minute walks, no structured exercise
- **Diet:** High in carbohydrates, low in fiber and iron-rich foods
- **Stress:** Moderate work-related stress
- **Weight Loss:** Recent 2 kg loss due to decreased appetite

### Review of Systems
- **General:** Fatigue, dizziness, unintended weight loss (2 kg in 6 months)
- **Cardiovascular:** Hypertension controlled with medication
- **Respiratory:** No issues
- **Gastrointestinal:** Occasional bloating
- **Genitourinary:** Increased urinary frequency during menstruation
- **Musculoskeletal:** Mild lower back pain around menstrual cycle
- **Neurological:** No issues

### Physical Examination
- **General Appearance:** Alert but fatigued, mild pallor
- **Vital Signs:**
  - Blood Pressure: 132/85 mmHg
  - Heart Rate: 87 bpm
  - Temperature: 36.8°C
  - BMI: 26.8 (Overweight)
- **Abdominal Examination:** Mild tenderness, no palpable masses
- **Pelvic Examination:** Enlarged uterus with irregular contours

### Diagnostic Studies
- **Pelvic Ultrasound:** Confirms multiple fibroids, largest 4.8 cm
- **MRI Findings:** No malignancy, normal endometrial thickness
- **CBC Panel:** Mild anemia (Hemoglobin: 10.2 g/dL)

### Assessment and Treatment Plan
#### Assessment
The most likely diagnosis is symptomatic uterine fibroids causing heavy bleeding, anemia, and chronic pelvic pain. Differential diagnoses include adenomyosis and endometrial hyperplasia.

#### Treatment Plan
- **Medical Management:**
  - Ferrous sulfate 325 mg daily for anemia
  - Ibuprofen 400 mg as needed for pain
- **Surgical Consultation:**
  - Evaluation for myomectomy or uterine artery embolization (UAE)
- **Lifestyle Modifications:**
  - Increase iron-rich foods (spinach, red meat, lentils)
  - Encourage moderate exercise like low-impact yoga

#### Follow-Up Plan
- Biopsy results review in 1 week
- Monitor hemoglobin levels every 3 months

### Final Summary
Jane Doe presents with chronic pelvic pain, menorrhagia, and symptomatic uterine fibroids, leading to anemia and fatigue. Initial treatment includes iron supplementation and pain management, with a planned surgical evaluation for potential myomectomy. Lifestyle and dietary changes have been recommended to improve her overall well-being and quality of life. She will return for a biopsy review and surgical consultation in one week to discuss next steps based on findings.
"""

if __name__ == "__main__":

    sections = get_sections(text)

    for s in sections:
        print(s[:150], "...")
        print()
        print("*" * 50)
        print()
