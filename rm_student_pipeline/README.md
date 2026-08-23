# DTU Student Data Pipeline & UI

A production-style Streamlit application for the CDIE / Recruitment Manager technical assessment at Delhi Technological University.

The application turns a deliberately messy student dataset into a recruitment-ready shortlist through a deterministic cleaning pipeline, live score filtering, eligibility controls, and one-click CSV export.

## Demo

**Live app:** _Add your deployed Streamlit URL here_

**90-second video:** _Add your unlisted YouTube / Google Drive / Loom URL here_

### 90-second demo script

0–10s — Open the dashboard and point out the purpose: “This app cleans raw student data and turns it into a live recruitment shortlist.”

10–25s — Upload the raw CSV or click **Use sample**. Show the cleaned row count and the **Data-cleaning report**. Mention that names, gender encodings, grades, and score strings are normalized automatically.

25–40s — Move **Minimum Total Score** from 180 to a higher value and show the shortlist count updating live. Briefly demonstrate grade/name filtering.

40–58s — Open **Active / Debarred controls**, search for a student, uncheck **Active**, and point out that the shortlist immediately excludes that student.

58–72s — Reset the status if desired, change the score threshold again, and show the shortlist statistics changing.

72–82s — Click **Export final shortlist as CSV** and mention that only currently eligible students are exported.

82–90s — End on the architecture / cleaning report and say: “The pipeline recalculates Total instead of trusting the source column and uses conservative duplicate handling to avoid merging legitimate students.”

## Features

- CSV upload with Excel support as a convenience.
- Automatic data cleaning and validation.
- Name normalization: whitespace, quotes/apostrophes, and casing.
- Gender normalization: `M/m/Male/0 → Male` and `F/f/Female/1 → Female`.
- Grade normalization from values such as `11` and `Grade 11`.
- Score parsing from values such as `28 marks`.
- Score validation to the expected `0–100` range.
- Deterministic missing-value treatment.
- Conservative duplicate removal after normalization.
- `Total` is always recalculated from Math + Science + English.
- Dynamic minimum Total Score filter.
- Additional grade, gender, and name filters.
- Real-time Active/Debarred controls.
- Debarred students are automatically excluded from shortlist results.
- Live shortlist statistics.
- CSV export of the final filtered shortlist.
- Unit tests for core cleaning logic.

## Architecture

```text
User upload
    │
    ▼
load_uploaded_file()
    │
    ▼
clean_student_data()
    ├── schema validation
    ├── text/category normalization
    ├── numeric parsing
    ├── score-range validation
    ├── duplicate removal
    ├── missing-value handling
    └── Total recalculation
    │
    ▼
Clean dataframe + CleaningReport
    │
    ├── live filters
    ├── Active/Debarred state
    └── shortlist
             │
             ▼
       CSV export
```

The Streamlit UI is kept intentionally thin: the cleaning rules live in `src/pipeline.py`, which makes the logic independently testable and easier to maintain.

## Data-cleaning logic

### 1. Schema validation

The pipeline requires:

`Name, Gender, Grade, Math, Science, English, Total`

An upload with missing required columns fails with a clear validation message rather than producing partial output.

### 2. Name normalization

Examples:

- `"Aarav"` → `Aarav`
- `Aditi'` → `Aditi`
- `  ROHAN  ` → `Rohan`

Repeated student names are preserved; names are **not** used as a unique identifier.

### 3. Gender normalization

The supplied assessment data uses several encodings. The pipeline maps:

- `M`, `m`, `Male`, `0` → `Male`
- `F`, `f`, `Female`, `1` → `Female`

Unknown values are preserved as title-cased categories rather than silently discarded.

### 4. Grade normalization

Both `11` and `Grade 11` become numeric grade `11`.

Grades outside `1–12` are treated as invalid and handled as missing before imputation.

### 5. Score parsing and validation

Values such as:

- `28`
- `28 marks`
- `"28 marks"`

are converted to numeric `28`.

Scores outside `0–100` are invalid. Missing/invalid score cells are filled using the subject median, with a safe zero fallback only when a full subject has no usable values.

### 6. Duplicate handling

Duplicate removal happens **after normalization**.

A row is considered a duplicate only when the normalized student attributes and all three subject scores match:

`Name + Gender + Grade + Math + Science + English`

This intentionally avoids fuzzy-merging students just because their names are similar. That is important in recruitment data because two legitimate students can share the same name.

### 7. Total validation

The source `Total` column is never trusted.

For every retained row:

```text
Total = Math + Science + English
```

The resulting value is written back into the cleaned dataframe and validated before the UI receives the data.

### 8. Eligibility

A student is eligible for the shortlist only when:

```text
Active == True
AND Total >= minimum selected score
AND any optional filters match
```

Debarment therefore affects the shortlist immediately without deleting the underlying student record.

## Performance choices

The app keeps the cleaned dataframe in Streamlit session state so the file is not reparsed on every interaction.

Filtering is performed with vectorized pandas operations, and the expensive cleaning step occurs only when a dataset is loaded or reloaded.

The shortlist table is derived from the cleaned in-memory dataframe, so slider and filter interactions do not require disk or network I/O.

## Local setup

### 1. Clone

```bash
git clone https://github.com/<your-username>/dtu-student-data-pipeline.git
cd dtu-student-data-pipeline
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run tests

```bash
python -m pytest -q
```

Expected result:

```text
4 passed
```

### 5. Start the app

```bash
streamlit run app.py
```

Then open the local URL printed by Streamlit.

## Deployment

The easiest deployment target is **Streamlit Community Cloud**.

1. Push the repository to GitHub.
2. Sign in to Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select `app.py` as the main file.
5. Deploy.
6. Open the generated public URL and test:
   - sample dataset loading
   - minimum Total filter
   - status toggle
   - shortlist exclusion
   - CSV export
7. Put the final URL into this README.

No secrets are required for this project.

## Repository structure

```text
dtu-student-data-pipeline/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── RM_Student_Selection_Dataset.csv
│   └── RM_Student_Selection_Dataset.xlsx
├── src/
│   ├── __init__.py
│   └── pipeline.py
└── tests/
    └── test_pipeline.py
```

## Validation performed on the assessment dataset

The supplied workbook contains 3,000 rows.

On the supplied data, the pipeline verifies:

- 3,000 cleaned rows retained.
- 0 duplicate normalized rows removed.
- 0 missing values required imputation.
- 9,000 score cells successfully parsed, including values containing the `marks` suffix.
- 3,000 totals recalculated.
- 0 source Total mismatches found.
- All subject scores fall within `0–100`.
- Every recalculated Total equals Math + Science + English.

The fact that the source `Total` is currently correct does not weaken the validation: the application still recomputes it, which prevents stale or corrupted totals from entering the shortlist.

## Engineering notes

### Why Streamlit?

For this assessment, Streamlit gives a strong balance between implementation speed and visible functionality: upload, filtering, editable controls, tables, and downloads can all be delivered in a small, testable Python codebase.

### Why not fuzzy duplicate matching by default?

Fuzzy matching on names can incorrectly merge two different students with similar names. The safer default is exact duplicate detection after deterministic normalization. This can be extended later if the university provides a stable student identifier.

### Why keep Active status separate from cleaning?

Cleaning transforms source data. Eligibility is an operational decision. Keeping `Active` as UI-managed state means debarment does not destroy source information and can be reversed immediately.

## Assessment-ready checklist

- [x] Upload and process raw student data
- [x] Clean names, genders, grades, and scores
- [x] Handle duplicates
- [x] Handle missing / invalid values
- [x] Recalculate and validate Total
- [x] Display cleaned data
- [x] Dynamic minimum Total Score filter
- [x] Live shortlist statistics
- [x] Active / Debarred toggle
- [x] Immediate shortlist exclusion for debarred students
- [x] CSV export
- [x] Automated tests
- [x] README with setup and cleaning logic
- [ ] Add deployed Streamlit URL
- [ ] Add 90-second demonstration video URL

## License

For academic assessment / demonstration use.
