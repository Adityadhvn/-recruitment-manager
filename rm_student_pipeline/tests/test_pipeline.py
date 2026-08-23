import pandas as pd
import pytest

from src.pipeline import clean_student_data, PipelineError


def test_dirty_values_are_normalized_and_total_recalculated():
    raw = pd.DataFrame(
        [
            {
                "Name": '" rohan\' ',
                "Gender": "m",
                "Grade": "Grade 3",
                "Math": "16 marks",
                "Science": 77,
                "English": "8 marks",
                "Total": 999,
            }
        ]
    )
    cleaned, report = clean_student_data(raw)
    row = cleaned.iloc[0]

    assert row["Name"] == "Rohan"
    assert row["Gender"] == "Male"
    assert row["Grade"] == 3
    assert row["Math"] == 16
    assert row["Total"] == 101
    assert report.total_mismatches_fixed == 1


def test_normalized_duplicate_rows_are_removed():
    raw = pd.DataFrame(
        [
            {"Name": "Aditi", "Gender": "F", "Grade": "11", "Math": "20 marks", "Science": 30, "English": 40, "Total": 0},
            {"Name": '"ADITI"', "Gender": "female", "Grade": "Grade 11", "Math": 20, "Science": "30 marks", "English": "40 marks", "Total": 999},
        ]
    )
    cleaned, report = clean_student_data(raw)
    assert len(cleaned) == 1
    assert report.duplicate_rows_removed == 1
    assert cleaned.iloc[0]["Total"] == 90


def test_missing_values_are_filled_and_scores_are_validated():
    raw = pd.DataFrame(
        [
            {"Name": "A", "Gender": None, "Grade": None, "Math": None, "Science": 40, "English": 50, "Total": 0},
            {"Name": "B", "Gender": "F", "Grade": "Grade 10", "Math": 100, "Science": "20 marks", "English": 30, "Total": 0},
        ]
    )
    cleaned, report = clean_student_data(raw)
    assert report.missing_values_filled > 0
    assert cleaned[["Math", "Science", "English"]].isna().sum().sum() == 0
    assert cleaned["Total"].between(0, 300).all()


def test_required_columns_are_validated():
    raw = pd.DataFrame({"Name": ["A"], "Math": [10]})
    with pytest.raises(PipelineError):
        clean_student_data(raw)
