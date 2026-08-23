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
    :root {
        --ink:#17201b;
        --muted:#68736d;
        --line:#dfe5e1;
        --green:#42624d;
        --soft:#f4f7f4;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--line);
    }

    [data-testid="stMetric"] {
        background: var(--soft);
        border: 1px solid var(--line);
        padding: 12px 14px;
        border-radius: 12px;
    }

    .rm-kicker {
        color: var(--green);
        text-transform: uppercase;
        letter-spacing:.13em;
        font-size:.74rem;
        font-weight:700;
    }

    .rm-title {
        font-size:2.25rem;
        line-height:1.1;
        font-weight:750;
        letter-spacing:-.035em;
        color:var(--ink);
        margin:0;
    }

    .rm-subtitle {
        color:var(--muted);
        margin-top:.45rem;
        margin-bottom:1.3rem;
    }

    .rm-note {
        color:var(--muted);
        font-size:.9rem;
    }

    .rm-card {
        background:white;
        border:1px solid var(--line);
        border-radius:14px;
        padding:1rem 1.1rem;
    }

    .rm-status {
        padding:.45rem .7rem;
        border-radius:999px;
        background:#e7f1e9;
        color:#31543b;
        font-weight:650;
        display:inline-block;
    }

    /* --------------------------------------------------------------
       DATAFRAME TOOLBAR
       -------------------------------------------------------------- */

    [data-testid="stElementToolbar"] button {
        width:36px !important;
        height:36px !important;
        min-width:36px !important;
        min-height:36px !important;
    }

    [data-testid="stElementToolbar"] button svg {
        width:20px !important;
        height:20px !important;
    }

    /* --------------------------------------------------------------
       CATEGORY TAB STYLING
       -------------------------------------------------------------- */

    div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap:0.35rem;
        padding:0.35rem;
        background:#f4f7f4;
        border:1px solid #dfe5e1;
        border-radius:14px;
        margin-bottom:1.35rem;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex:1 1 0;
        justify-content:center;
        padding:0.72rem 0.85rem;
        border-radius:10px;
        cursor:pointer;
        font-weight:650;
        color:#68736d;
        transition:all 0.15s ease;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background:#e9efea;
        color:#17201b;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background:#ffffff;
        color:#17201b;
        box-shadow:0 1px 5px rgba(23, 32, 27, 0.10);
        border:1px solid #dfe5e1;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display:none;
    }

    /* --------------------------------------------------------------
       IMPORTANT VALUES
       -------------------------------------------------------------- */

    [data-testid="stMetricValue"] {
        font-weight:800;
    }

    .rm-section-title {
        font-size:1.25rem;
        font-weight:800;
        color:#17201b;
        margin-bottom:0.25rem;
    }

    .rm-important {
        font-weight:750;
        color:#17201b;
    }

    /* --------------------------------------------------------------
       MOBILE RESPONSIVE OPTIMIZATION
       Desktop styles above remain unchanged.
       -------------------------------------------------------------- */

    @media (max-width: 768px) {

        /* Page spacing */
        .block-container {
            padding-top:2rem;
            padding-left:0.85rem;
            padding-right:0.85rem;
            padding-bottom:2rem;
        }

        /* Header */
        .rm-kicker {
            font-size:0.65rem;
            letter-spacing:0.11em;
        }

        .rm-title {
            font-size:1.75rem;
            line-height:1.08;
            letter-spacing:-0.03em;
        }

        .rm-subtitle {
            font-size:0.88rem;
            line-height:1.45;
            margin-top:0.4rem;
            margin-bottom:1rem;
        }

        /* ----------------------------------------------------------
           CATEGORY TABS
           4 tabs become a clean 2 x 2 mobile layout.
           ---------------------------------------------------------- */

        div[data-testid="stRadio"] > div[role="radiogroup"] {
            display:flex;
            flex-wrap:wrap;
            gap:0.3rem;
            padding:0.3rem;
            margin-bottom:1rem;
        }

        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            flex:0 0 calc(50% - 0.15rem);
            width:calc(50% - 0.15rem);
            min-height:44px;
            padding:0.55rem 0.4rem;
            text-align:center;
            line-height:1.2;
            font-size:0.78rem;
            display:flex;
            align-items:center;
        }

        /* ----------------------------------------------------------
           KPI / METRIC COLUMNS
           Prevent 5 metrics from becoming squeezed on mobile.
           ---------------------------------------------------------- */

        [data-testid="stHorizontalBlock"] {
            flex-wrap:wrap !important;
            gap:0.5rem !important;
        }

        [data-testid="stHorizontalBlock"] > div {
            flex:0 0 calc(50% - 0.25rem) !important;
            width:calc(50% - 0.25rem) !important;
            min-width:0 !important;
        }

        [data-testid="stMetric"] {
            padding:10px 11px;
            border-radius:10px;
        }

        [data-testid="stMetricLabel"] {
            font-size:0.75rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size:1.25rem !important;
            line-height:1.15 !important;
        }

        /* ----------------------------------------------------------
           SECTION HEADINGS
           ---------------------------------------------------------- */

        .rm-section-title {
            font-size:1.1rem;
            margin-top:0.2rem;
        }

        /* ----------------------------------------------------------
           DATAFRAME TOOLBAR
           Keep buttons comfortably tappable on phones.
           ---------------------------------------------------------- */

        [data-testid="stElementToolbar"] {
            gap:0.2rem !important;
        }

        [data-testid="stElementToolbar"] button {
            width:38px !important;
            height:38px !important;
            min-width:38px !important;
            min-height:38px !important;
        }

        [data-testid="stElementToolbar"] button svg {
            width:20px !important;
            height:20px !important;
        }

        /* ----------------------------------------------------------
           DATAFRAMES
           Preserve horizontal scrolling for wide tables.
           ---------------------------------------------------------- */

        [data-testid="stDataFrame"] {
            width:100% !important;
        }

        /* ----------------------------------------------------------
           SIDEBAR
           ---------------------------------------------------------- */

        [data-testid="stSidebar"] {
            min-width:0 !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding-left:1rem;
            padding-right:1rem;
        }

        /* Sidebar upload buttons remain side-by-side */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
            flex-wrap:nowrap !important;
        }

        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
            flex:1 1 0 !important;
            width:auto !important;
        }

        /* ----------------------------------------------------------
           DOWNLOAD BUTTON
           Full-width and easier to tap on mobile.
           ---------------------------------------------------------- */

        div[data-testid="stDownloadButton"] button {
            width:100%;
            min-height:44px;
        }

        /* ----------------------------------------------------------
           SEARCH / TEXT INPUTS
           ---------------------------------------------------------- */

        input,
        textarea {
            font-size:16px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DISPLAY_COLUMNS = [
    "Student ID",
    "Name",
    "Gender",
    "Grade",
    "Math",
    "Science",
    "English",
    "Total",
    "Active",
]

CATEGORY_OPTIONS = {
    "live": "Live Shortlist",
    "report": "View Cleaning Report",
    "cleaned": "Full Cleaned Dataset",
    "manage": "Manage Active / Debarred Students",
}


def _init_state() -> None:
    st.session_state.setdefault("df", None)
    st.session_state.setdefault("report", None)
    st.session_state.setdefault("source_name", None)


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


def _read_sample() -> None:
    with SAMPLE_FILE.open("rb") as handle:
        _load_and_clean(handle, SAMPLE_FILE.name)


def _column_config() -> dict:
    """Shared column formatting for the shortlist and full-dataset tables."""
    return {
        "Total": st.column_config.ProgressColumn(
            "Total", min_value=0, max_value=300, format="%d"
        ),
        "Active": st.column_config.CheckboxColumn("Active", disabled=True),
    }


def _status_editor(df: pd.DataFrame) -> None:
    st.markdown("### Active / Debarred controls")
    st.markdown("**Active = ELIGIBLE.**")
    st.markdown("**Uncheck Active = DEBARRED AND EXCLUDED FROM SHORTLIST.**")

    query = st.text_input(
        "**Find a student**",
        placeholder="Search by student name or ID",
        key="status_search",
    ).strip()

    editable = df[["Student ID", "Name", "Grade", "Total", "Active"]].copy()

    if query:
        mask = editable["Name"].str.contains(
            query, case=False, na=False
        ) | editable["Student ID"].str.contains(query, case=False, na=False)
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
                help=(
                    "Uncheck to debar. Debarred students are "
                    "excluded from shortlist results."
                ),
                default=True,
            ),
            "Total": st.column_config.NumberColumn("Total", format="%d"),
        },
        key="status_editor",
    )

    # Persist only status changes, leaving the cleaned dataset immutable.
    status_map = dict(zip(edited["Student ID"], edited["Active"]))
    df_ids = st.session_state.df["Student ID"]
    st.session_state.df.loc[df_ids.isin(status_map), "Active"] = (
        df_ids.map(status_map).fillna(st.session_state.df["Active"])
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("1. Load dataset")

        uploaded = st.file_uploader(
            "Upload raw student CSV",
            type=["csv", "xlsx", "xls"],
            help="CSV is the assessment format; Excel is accepted as a convenience.",
        )

        col1, col2 = st.columns(2)
        with col1:
            process_clicked = st.button(
                "Process upload", use_container_width=True, type="primary"
            )
        with col2:
            sample_clicked = st.button("Use sample", use_container_width=True)

        if process_clicked and uploaded:
            _load_and_clean(uploaded, uploaded.name)
        if sample_clicked:
            _read_sample()

        st.divider()
        st.header("2. Shortlist filter")

        if st.session_state.df is None:
            st.caption("Load a dataset to enable filtering.")
            return

        df = st.session_state.df
        max_total = int(df["Total"].max())

        st.slider(
            "Minimum Total Score",
            min_value=0,
            max_value=max_total,
            value=min(180, max_total),
            step=1,
            key="min_total",
        )

        grade_options = sorted(df["Grade"].dropna().astype(int).unique().tolist())
        st.multiselect(
            "Grade", options=grade_options, placeholder="All grades", key="grade_filter"
        )
        st.multiselect(
            "Gender",
            options=sorted(df["Gender"].unique().tolist()),
            placeholder="All genders",
            key="gender_filter",
        )
        st.text_input("Name search", placeholder="Type a name...", key="name_filter")


def _apply_shortlist_filters(df: pd.DataFrame) -> pd.DataFrame:
    min_total = st.session_state.get("min_total", 180)
    grade_filter = st.session_state.get("grade_filter", [])
    gender_filter = st.session_state.get("gender_filter", [])
    name_filter = st.session_state.get("name_filter", "").strip()

    shortlist = df[df["Active"]].copy()
    shortlist = shortlist[shortlist["Total"] >= min_total]

    if grade_filter:
        shortlist = shortlist[shortlist["Grade"].isin(grade_filter)]
    if gender_filter:
        shortlist = shortlist[shortlist["Gender"].isin(gender_filter)]
    if name_filter:
        shortlist = shortlist[
            shortlist["Name"].str.contains(name_filter, case=False, na=False)
        ]

    return shortlist


def _render_live_shortlist(df: pd.DataFrame, shortlist: pd.DataFrame) -> None:
    avg_total = shortlist["Total"].mean() if not shortlist.empty else 0

    cols = st.columns(5)
    cols[0].metric("Loaded", f"{len(df):,}")
    cols[1].metric("Active", f"{int(df['Active'].sum()):,}")
    cols[2].metric("Debarred", f"{int((~df['Active']).sum()):,}")
    cols[3].metric("Shortlisted", f"{len(shortlist):,}")
    cols[4].metric("Avg. shortlist", f"{avg_total:.1f}")

    st.markdown('<div class="rm-section-title">Live Shortlist</div>', unsafe_allow_html=True)

    min_total = st.session_state.get("min_total", 180)
    eligibility_text = (
        f'<span class="rm-important">Eligibility:</span> '
        f'Active students with <span class="rm-important">Total ≥ {min_total}</span>'
    )
    filters_active = (
        st.session_state.get("grade_filter")
        or st.session_state.get("gender_filter")
        or st.session_state.get("name_filter")
    )
    eligibility_text += (
        " plus the selected grade, gender, and/or name filters."
        if filters_active
        else "."
    )
    st.markdown(eligibility_text, unsafe_allow_html=True)

    st.dataframe(
        shortlist[DISPLAY_COLUMNS],
        hide_index=True,
        use_container_width=True,
        height=480,
        column_config=_column_config(),
    )

    st.download_button(
        "**Export final shortlist as CSV**",
        data=dataframe_to_csv_bytes(shortlist[DISPLAY_COLUMNS]),
        file_name="dtu_shortlist.csv",
        mime="text/csv",
        type="primary",
    )


def _render_cleaning_report() -> None:
    report: CleaningReport = st.session_state.report

    st.markdown('<div class="rm-section-title">Cleaning Report</div>', unsafe_allow_html=True)
    st.markdown(
        "Review the **data-quality changes** performed "
        "before the dataset was made available for recruitment.",
    )

    rcols = st.columns(5)
    rcols[0].metric("Input rows", f"{report.input_rows:,}")
    rcols[1].metric("Rows removed", f"{report.duplicate_rows_removed:,}")
    rcols[2].metric("Values filled", f"{report.missing_values_filled:,}")
    rcols[3].metric("Score strings parsed", f"{report.score_values_parsed:,}")
    rcols[4].metric("Total corrections", f"{report.total_mismatches_fixed:,}")

    st.markdown("### What was cleaned")
    st.markdown(
        """
        - **Names, gender, and grades** were normalized.
        - **Score strings** were parsed into usable numeric values.
        - **Invalid score ranges** were validated.
        - **Missing values** were filled deterministically.
        - **Duplicate normalized rows** were removed.
        - **Total scores** were recalculated from the cleaned component scores.
        """
    )
    st.markdown(f"**Source dataset:** `{st.session_state.source_name}`")


def _render_full_dataset(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="rm-section-title">Full Cleaned Dataset</div>', unsafe_allow_html=True
    )
    st.markdown(
        f"Showing **all {len(df):,} cleaned student records**, "
        "including **active and debarred students**.",
    )

    st.dataframe(
        df[DISPLAY_COLUMNS],
        hide_index=True,
        use_container_width=True,
        height=520,
        column_config=_column_config(),
    )

    st.download_button(
        "**Download full cleaned dataset as CSV**",
        data=dataframe_to_csv_bytes(df[DISPLAY_COLUMNS]),
        file_name="dtu_full_cleaned_dataset.csv",
        mime="text/csv",
    )


def main() -> None:
    _init_state()

    st.markdown('<div class="rm-kicker"> "   "  </div>', unsafe_allow_html=True)
    st.markdown('<div class="rm-title">Student Data Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rm-subtitle">Clean, validate, shortlist, control eligibility, '
        'and export recruitment-ready student data.</div>',
        unsafe_allow_html=True,
    )

    _render_sidebar()

    if st.session_state.df is None:
        st.info("Start by loading the assessment dataset from the sidebar.")
        st.markdown("### What this app demonstrates")
        st.markdown(
            "Automated cleaning • duplicate handling • score parsing • "
            "missing-value treatment • Total recalculation • "
            "live shortlisting • eligibility control • CSV export"
        )
        return

    df = st.session_state.df
    shortlist = _apply_shortlist_filters(df)

    # ------------------------------------------------------------------
    # CATEGORY TABS
    #
    # These are intentionally implemented as a single-select horizontal
    # control rather than st.tabs(), because only the selected category
    # should be rendered as the active content area.
    # ------------------------------------------------------------------
    st.session_state.setdefault("active_category", "live")

    selected = st.radio(
        "Category",
        options=list(CATEGORY_OPTIONS.keys()),
        format_func=lambda key: CATEGORY_OPTIONS[key],
        horizontal=True,
        key="active_category",
        label_visibility="collapsed",
    )

    if selected == "live":
        _render_live_shortlist(df, shortlist)
    elif selected == "report":
        _render_cleaning_report()
    elif selected == "cleaned":
        _render_full_dataset(df)
    elif selected == "manage":
        st.markdown(
            '<div class="rm-section-title">Manage Active / Debarred Students</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Use the **Active** checkbox to control student eligibility. "
            "**Debarred students are automatically excluded from the Live Shortlist.**"
        )
        _status_editor(df)


if __name__ == "__main__":
    main()