# DTU Student Data Pipeline & UI

A Streamlit app that turns a messy student dataset into a recruitment-ready shortlist through a deterministic cleaning pipeline, live filtering, eligibility controls, and CSV export.

## Demo

**Live app:** _Add your deployed Streamlit URL here_

**90-second video:** _Add your demo video URL here_

## Features

- Upload CSV (or Excel) and auto-clean it
- Name, gender, and grade normalization
- Score parsing (e.g. `28 marks` → `28`) and range validation (0–100)
- Deterministic missing-value imputation
- Conservative duplicate removal (post-normalization, exact match only)
- `Total` always recalculated from Math + Science + English — source `Total` is never trusted
- Live filtering by minimum Total, grade, gender, and name
- Active/Debarred toggle with immediate shortlist exclusion
- CSV export of the current shortlist
- Unit-tested cleaning logic

## Architecture

```text
Upload → load_uploaded_file() → clean_student_data() → Clean dataframe + CleaningReport
                                                                │
                                                    filters, Active/Debarred state
                                                                │
                                                           Shortlist → CSV export
```

The UI (`app.py`) is kept thin — all cleaning rules live in `src/pipeline.py`, independently testable and easy to maintain.

## Cleaning logic

| Step | Rule |
|---|---|
| **Schema** | Requires `Name, Gender, Grade, Math, Science, English, Total`; fails fast with a clear message if columns are missing |
| **Name** | Trims whitespace/quotes, collapses spaces, title-cases (`"  ROHAN  "` → `Rohan`) |
| **Gender** | Maps `M/m/Male/0` → `Male`, `F/f/Female/1` → `Female`; unknown values kept as title-cased categories |
| **Grade** | Extracts numeric grade (`Grade 11` → `11`); values outside 1–12 treated as missing |
| **Scores** | Parses numeric value from strings like `28 marks`; values outside 0–100 treated as missing |
| **Missing values** | Filled with the subject/grade median (zero fallback only if a whole column has no usable values) |
| **Duplicates** | Removed only when Name + Gender + Grade + all three scores match exactly, post-normalization — avoids merging different students who share a name |
| **Total** | Always recomputed as Math + Science + English; source `Total` is discarded |

## Eligibility

A student appears in the shortlist only when:

```text
Active == True AND Total >= minimum selected score AND any optional filters match
```

Debarring a student updates the shortlist immediately without deleting their record.

## Local setup

```bash
git clone https://github.com/<your-username>/dtu-student-data-pipeline.git
cd dtu-student-data-pipeline

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python -m pytest -q            # expect: 4 passed
streamlit run app.py
```

## Deployment (Streamlit Community Cloud)

1. Push the repo to GitHub.
2. Create a new app on Streamlit Community Cloud, pointing to `app.py`.
3. Deploy, then verify: sample dataset loads, filters work, debarring excludes a student, CSV export works.
4. Add the live URL to this README.

No secrets required.

## Repository structure

```text
dtu-student-data-pipeline/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml
├── data/
│   ├── RM_Student_Selection_Dataset.csv
│   └── RM_Student_Selection_Dataset.xlsx
├── src/
│   ├── __init__.py
│   └── pipeline.py
└── tests/
    └── test_pipeline.py
```

## Validation on the assessment dataset (3,000 rows)

- 3,000 rows retained, 0 duplicates removed, 0 missing-value imputations needed
- 9,000 score cells parsed successfully (including `marks`-suffixed values)
- All 3,000 Totals recalculated; 0 mismatches vs. source `Total`
- Every score falls within 0–100, and every Total equals Math + Science + English

The source `Total` happening to be correct doesn't change the approach — it's still recomputed, so a stale or corrupted total can never reach the shortlist.

## Design notes

- **Streamlit** was chosen for speed: upload, filtering, editable tables, and downloads in a small, testable codebase.
- **No fuzzy duplicate matching** — exact matching after normalization avoids merging two different students with similar names. Can be extended if a stable student ID becomes available.
- **Active status is separate from cleaning** — cleaning transforms source data; eligibility is an operational decision. Keeping `Active` as UI-managed state means debarment is reversible and never destroys source data.


## License

For academic assessment / demonstration use.
