from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = ["Name", "Gender", "Grade", "Math", "Science", "English", "Total"]
SCORE_COLUMNS = ["Math", "Science", "English"]

GENDER_MAP = {
    "m": "Male",
    "male": "Male",
    "0": "Male",
    "f": "Female",
    "female": "Female",
    "1": "Female",
}


@dataclass
class CleaningReport:
    input_rows: int
    output_rows: int
    duplicate_rows_removed: int
    missing_values_filled: int
    score_values_parsed: int
    totals_recalculated: int
    total_mismatches_fixed: int


class PipelineError(ValueError):
    """Raised when an uploaded dataset cannot be processed safely."""


def load_uploaded_file(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    """Read CSV/XLSX into a dataframe with a helpful validation error."""
    suffix = filename.lower().rsplit(".", 1)[-1]
    try:
        if suffix == "csv":
            return pd.read_csv(file_obj)
        if suffix in {"xlsx", "xls"}:
            return pd.read_excel(file_obj)
    except Exception as exc:
        raise PipelineError(f"Could not read '{filename}': {exc}") from exc

    raise PipelineError("Unsupported file type. Please upload a CSV or Excel file.")


def _clean_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    return float(match.group())


def _clean_name(value: object) -> str:
    if pd.isna(value) or not str(value).strip():
        return "Unknown Student"
    text = str(value).strip()
    text = text.replace('"', "").replace("'", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.title()


def _clean_gender(value: object) -> str:
    if pd.isna(value) or not str(value).strip():
        return "Unknown"
    key = str(value).strip().lower()
    return GENDER_MAP.get(key, key.title())


def _clean_grade(value: object) -> float | None:
    if pd.isna(value) or not str(value).strip():
        return None
    match = re.search(r"\d+", str(value))
    return float(match.group()) if match else None


def _student_id(row: pd.Series, sequence: int) -> str:
    """Stable-ish human-friendly ID; sequence guarantees uniqueness for collisions."""
    canonical = "|".join(
        [
            str(row.get("Name", "")),
            str(row.get("Gender", "")),
            str(row.get("Grade", "")),
            str(row.get("Math", "")),
            str(row.get("Science", "")),
            str(row.get("English", "")),
        ]
    )
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:6].upper()
    return f"DTU-{digest}-{sequence:04d}"


def clean_student_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """
    Clean and validate student data.

    Rules:
    - Require the seven assessment columns.
    - Normalize names, gender encodings, grades, and score strings.
    - Parse values such as '28 marks' to numeric scores.
    - Validate scores to 0-100; invalid/out-of-range values become missing.
    - Impute missing score values with the subject median; missing grades with
      the rounded grade median.
    - Recalculate Total from Math + Science + English and never trust source Total.
    - Remove duplicate rows after normalization.
    - Add Active=True and a unique Student ID.
    """
    if raw is None or raw.empty:
        raise PipelineError("The uploaded file contains no rows.")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing_cols:
        raise PipelineError(
            "Missing required columns: " + ", ".join(missing_cols)
        )

    df = raw[REQUIRED_COLUMNS].copy()
    input_rows = len(df)

    # Clean categorical/text fields.
    df["Name"] = df["Name"].map(_clean_name)
    df["Gender"] = df["Gender"].map(_clean_gender)
    df["Grade"] = df["Grade"].map(_clean_grade)

    # Parse numeric score fields and track how many non-numeric strings were fixed.
    parse_count = 0
    for col in SCORE_COLUMNS:
        original = df[col].copy()
        cleaned = original.map(_clean_number)
        parse_count += int((original.map(lambda x: isinstance(x, str) and bool(re.search(r"[A-Za-z]", x))) & cleaned.notna()).sum())
        df[col] = pd.to_numeric(cleaned, errors="coerce")
        df.loc[~df[col].between(0, 100, inclusive="both"), col] = pd.NA

    # Grade validation.
    df.loc[~df["Grade"].between(1, 12, inclusive="both"), "Grade"] = pd.NA

    # De-duplicate after normalization. This is conservative: exact cleaned-row
    # duplicates are removed, while legitimately repeated names are retained.
    before_dedup = len(df)
    df = df.drop_duplicates(
        subset=["Name", "Gender", "Grade", "Math", "Science", "English"],
        keep="first",
    ).reset_index(drop=True)
    duplicate_rows_removed = before_dedup - len(df)

    # Impute missing values deterministically.
    missing_before = int(df[SCORE_COLUMNS + ["Grade", "Gender"]].isna().sum().sum())
    for col in SCORE_COLUMNS:
        median = df[col].median()
        df[col] = df[col].fillna(0 if pd.isna(median) else median)
    grade_median = df["Grade"].median()
    df["Grade"] = df["Grade"].fillna(round(grade_median) if pd.notna(grade_median) else 0)
    df["Gender"] = df["Gender"].fillna("Unknown")
    df["Grade"] = df["Grade"].round().astype("Int64")
    missing_values_filled = missing_before

    # Total is always recomputed.
    source_total = df["Total"] if "Total" in df.columns else pd.Series(index=df.index, dtype=float)
    source_total_num = source_total.map(_clean_number)
    calculated_total = df[SCORE_COLUMNS].sum(axis=1).round().astype(int)
    total_mismatches_fixed = int(
        (source_total_num.fillna(-1).round() != calculated_total).sum()
    )
    df["Total"] = calculated_total

    # Stable ordering makes the app and exported CSV reproducible.
    df.insert(
        0,
        "Student ID",
        [_student_id(row, i + 1) for i, (_, row) in enumerate(df.iterrows())],
    )
    df["Active"] = True

    # Final validation.
    for col in SCORE_COLUMNS:
        if not df[col].between(0, 100).all():
            raise PipelineError(f"Validation failed: {col} contains an invalid score.")
    if not df["Total"].eq(df[SCORE_COLUMNS].sum(axis=1)).all():
        raise PipelineError("Validation failed: Total is inconsistent with subject scores.")

    report = CleaningReport(
        input_rows=input_rows,
        output_rows=len(df),
        duplicate_rows_removed=duplicate_rows_removed,
        missing_values_filled=missing_values_filled,
        score_values_parsed=parse_count,
        totals_recalculated=len(df),
        total_mismatches_fixed=total_mismatches_fixed,
    )
    return df, report


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return UTF-8 CSV bytes suitable for st.download_button."""
    export_df = df.copy()
    return export_df.to_csv(index=False).encode("utf-8")
