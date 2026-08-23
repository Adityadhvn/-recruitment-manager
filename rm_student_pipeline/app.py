from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from pipeline import (  # noqa: E402
    CleaningReport,
    PipelineError,
    clean_student_data,
    dataframe_to_csv_bytes,
    load_uploaded_file,
)

st.set_page_config(
    page_title="DTU Recruitment Manager | Student Pipeline",
    page_icon="RM",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAMPLE_FILE = ROOT / "data" / "RM_Student_Selection_Dataset.xlsx"

# --- Styling: restrained, professional dashboard ---
st.markdown(
    """
    <style>
    :root { --ink:#17201b; --muted:#68736d; --line:#dfe5e1; --green:#42624d; --soft:#f4f7f4; }
    .block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { border-right: 1px solid var(--line); }
    [data-testid="stMetric"] { background: var(--soft); border: 1px solid var(--line); padding: 12px 14px; border-radius: 12px; }
    .rm-kicker { color: var(--green); text-transform: uppercase; letter-spacing:.13em; font-size:.74rem; font-weight:700; }
    .rm-title { font-size:2.25rem; line-height:1.1; font-weight:750; letter-spacing:-.035em; color:var(--ink); margin:0; }
    .rm-subtitle { color:var(--muted); margin-top:.45rem; margin-bottom:1.3rem; }
    .rm-note { color:var(--muted); font-size:.9rem; }
    .rm-card { background:white; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; }
    .rm-status { padding:.45rem .7rem; border-radius:999px; background:#e7f1e9; color:#31543b; font-weight:650; display:inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "df" not in st.session_state:
        st.session_state.df = None
    if "report" not in st.session_state:
        st.session_state.report = None
    if "source_name" not in st.session_state:
        st.session_state.source_name = None


def _load_and_clean(file_obj, filename: str) -> None:
    try:
        raw = load_uploaded_file(file_obj, filename)
        cleaned, report = clean_student_data(raw)
        st.session_state.df = cleaned
        st.session_state.report = report
        st.session_state.source_name = filename
    except PipelineError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Unexpected processing error: {exc}")


def _read_sample():
    with SAMPLE_FILE.open("rb") as handle:
        _load_and_clean(handle, SAMPLE_FILE.name)


def _status_editor(df: pd.DataFrame) -> None:
    st.markdown("### Active / Debarred controls")
    st.caption(
        "Change Active to False to debar a student. The shortlist updates immediately."
    )

    q = st.text_input(
        "Find a student",
        placeholder="Search by student name or ID",
        key="status_search",
    )
    editable = df[["Student ID", "Name", "Grade", "Total", "Active"]].copy()
    if q.strip():
        mask = (
            editable["Name"].str.contains(q.strip(), case=False, na=False)
            | editable["Student ID"].str.contains(q.strip(), case=False, na=False)
        )
        editable = editable.loc[mask]

    if editable.empty:
        st.info("No students match that search.")
        return

    edited = st.data_editor(
        editable,
        hide_index=True,
        use_container_width=True,
        height=360,
        disabled=["Student ID", "Name", "Grade", "Total"],
        column_config={
            "Active": st.column_config.CheckboxColumn(
                "Active",
                help="Uncheck to debar. Debarred students are excluded from shortlist results.",
                default=True,
            ),
            "Total": st.column_config.NumberColumn("Total", format="%d"),
        },
        key="status_editor",
    )

    # Persist only status changes, leaving the cleaned dataset immutable.
    status_map = dict(zip(edited["Student ID"], edited["Active"]))
    st.session_state.df.loc[
        st.session_state.df["Student ID"].isin(status_map.keys()), "Active"
    ] = st.session_state.df["Student ID"].map(status_map).fillna(
        st.session_state.df["Active"]
    )


def main() -> None:
    _init_state()

    st.markdown('<div class="rm-kicker">CDIE • Recruitment Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="rm-title">Student Data Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rm-subtitle">Clean, validate, shortlist, control eligibility, and export recruitment-ready student data.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("1. Load dataset")
        uploaded = st.file_uploader(
            "Upload raw student CSV",
            type=["csv", "xlsx", "xls"],
            help="CSV is the assessment format; Excel is accepted as a convenience.",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Process upload", use_container_width=True, type="primary") and uploaded:
                _load_and_clean(uploaded, uploaded.name)
        with c2:
            if st.button("Use sample", use_container_width=True):
                _read_sample()

        st.divider()
        st.header("2. Shortlist filter")
        if st.session_state.df is None:
            st.caption("Load a dataset to enable filtering.")
        else:
            max_total = int(st.session_state.df["Total"].max())
            min_total = st.slider(
                "Minimum Total Score",
                min_value=0,
                max_value=max_total,
                value=min(180, max_total),
                step=1,
                key="min_total",
            )
            grade_options = sorted(st.session_state.df["Grade"].dropna().astype(int).unique().tolist())
            grade_filter = st.multiselect(
                "Grade",
                options=grade_options,
                placeholder="All grades",
                key="grade_filter",
            )
            gender_filter = st.multiselect(
                "Gender",
                options=sorted(st.session_state.df["Gender"].unique().tolist()),
                placeholder="All genders",
                key="gender_filter",
            )
            name_filter = st.text_input(
                "Name search",
                placeholder="Type a name...",
                key="name_filter",
            )

    if st.session_state.df is None:
        st.info("Start by loading the assessment dataset from the sidebar.")
        st.markdown("### What this app demonstrates")
        st.markdown(
            "Automated cleaning • duplicate handling • score parsing • missing-value treatment • "
            "Total recalculation • live shortlisting • eligibility control • CSV export"
        )
        return

    df = st.session_state.df

    # Sidebar filters are available only after data is loaded.
    min_total = st.session_state.get("min_total", 180)
    grade_filter = st.session_state.get("grade_filter", [])
    gender_filter = st.session_state.get("gender_filter", [])
    name_filter = st.session_state.get("name_filter", "")

    active_df = df[df["Active"]].copy()
    shortlist = active_df[active_df["Total"] >= min_total].copy()
    if grade_filter:
        shortlist = shortlist[shortlist["Grade"].isin(grade_filter)]
    if gender_filter:
        shortlist = shortlist[shortlist["Gender"].isin(gender_filter)]
    if name_filter.strip():
        shortlist = shortlist[
            shortlist["Name"].str.contains(name_filter.strip(), case=False, na=False)
        ]

    # KPI row
    avg_total = shortlist["Total"].mean() if not shortlist.empty else 0
    cols = st.columns(5)
    cols[0].metric("Loaded", f"{len(df):,}")
    cols[1].metric("Active", f"{int(df['Active'].sum()):,}")
    cols[2].metric("Debarred", f"{int((~df['Active']).sum()):,}")
    cols[3].metric("Shortlisted", f"{len(shortlist):,}")
    cols[4].metric("Avg. shortlist", f"{avg_total:.1f}")

    st.markdown("### Live shortlist")
    st.caption(
        f"Eligibility = Active students with Total ≥ {min_total}"
        + (" plus selected grade/gender/search filters." if (grade_filter or gender_filter or name_filter) else ".")
    )

    display_cols = ["Student ID", "Name", "Gender", "Grade", "Math", "Science", "English", "Total", "Active"]
    st.dataframe(
        shortlist[display_cols],
        hide_index=True,
        use_container_width=True,
        height=480,
        column_config={
            "Total": st.column_config.ProgressColumn(
                "Total",
                min_value=0,
                max_value=300,
                format="%d",
            ),
            "Active": st.column_config.CheckboxColumn("Active", disabled=True),
        },
    )

    export_bytes = dataframe_to_csv_bytes(shortlist[display_cols])
    st.download_button(
        "Export final shortlist as CSV",
        data=export_bytes,
        file_name="dtu_shortlist.csv",
        mime="text/csv",
        type="primary",
    )

    with st.expander("Data-cleaning report", expanded=False):
        report: CleaningReport = st.session_state.report
        rcols = st.columns(5)
        rcols[0].metric("Input rows", f"{report.input_rows:,}")
        rcols[1].metric("Rows removed", f"{report.duplicate_rows_removed:,}")
        rcols[2].metric("Values filled", f"{report.missing_values_filled:,}")
        rcols[3].metric("Score strings parsed", f"{report.score_values_parsed:,}")
        rcols[4].metric("Total corrections", f"{report.total_mismatches_fixed:,}")
        st.write(
            "The pipeline normalizes names/gender/grades, parses score strings, validates score ranges, "
            "fills missing values deterministically, removes duplicate normalized rows, and recalculates Total."
        )

    with st.expander("Manage Active / Debarred status"):
        _status_editor(df)

    with st.expander("Cleaned dataset"):
        st.dataframe(df[display_cols], hide_index=True, use_container_width=True, height=420)


if __name__ == "__main__":
    main()
