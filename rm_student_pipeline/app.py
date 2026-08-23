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

# ---------------------------------------------------------------------------
# UI styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --ink: #17201b;
        --muted: #68736d;
        --line: rgba(73, 98, 82, 0.16);
        --green: #42624d;
        --green-2: #315f43;
        --soft: #f4f7f4;
        --glass: rgba(255, 255, 255, 0.74);
    }

    /* Page */
    .stApp {
        background:
            radial-gradient(circle at 72% 0%, rgba(119, 157, 130, 0.10), transparent 34%),
            linear-gradient(180deg, #fbfcfb 0%, #f7f9f7 100%);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.25rem;
        padding-bottom: 3.5rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--line);
        background: rgba(248, 250, 248, 0.92);
    }

    .rm-focus-mode [data-testid="stSidebar"] {
        display: none !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
    }

    /* Header */
    .rm-kicker {
        color: var(--green);
        text-transform: uppercase;
        letter-spacing: .13em;
        font-size: .72rem;
        font-weight: 750;
        margin-bottom: .3rem;
    }

    .rm-title {
        font-size: 2.35rem;
        line-height: 1.05;
        font-weight: 780;
        letter-spacing: -.045em;
        color: var(--ink);
        margin: 0;
    }

    .rm-subtitle {
        color: var(--muted);
        margin-top: .45rem;
        margin-bottom: 1.15rem;
        font-size: .96rem;
    }

    /* Floating glass navigation */
    .rm-nav-shell {
        position: sticky;
        top: .7rem;
        z-index: 20;
        margin: .55rem 0 1.25rem;
        padding: .38rem;
        border: 1px solid rgba(255,255,255,.82);
        border-radius: 18px;
        background: rgba(255,255,255,.62);
        backdrop-filter: blur(18px) saturate(155%);
        -webkit-backdrop-filter: blur(18px) saturate(155%);
        box-shadow:
            0 12px 34px rgba(37, 57, 44, .08),
            inset 0 1px 0 rgba(255,255,255,.9);
    }

    /* Streamlit tabs are rendered after the shell marker. */
    .rm-nav-shell + div [data-baseweb="tab-list"] {
        gap: .25rem;
        padding: .16rem;
        border: 1px solid rgba(66,98,77,.08);
        border-radius: 15px;
        background: rgba(246,249,246,.58);
    }

    .rm-nav-shell + div [data-baseweb="tab"] {
        min-height: 54px;
        padding: 0 1.15rem;
        border-radius: 12px;
        color: #66716a;
        font-weight: 650;
        font-size: .91rem;
        transition: all .18s ease;
    }

    .rm-nav-shell + div [data-baseweb="tab"]:hover {
        color: var(--green-2);
        background: rgba(255,255,255,.72);
    }

    .rm-nav-shell + div [aria-selected="true"] {
        color: var(--green-2) !important;
        background: rgba(255,255,255,.96) !important;
        box-shadow: 0 4px 14px rgba(42,65,49,.08);
    }

    .rm-nav-shell + div [data-baseweb="tab-highlight"] {
        background: var(--green) !important;
        height: 3px !important;
        border-radius: 999px;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,.82);
        border: 1px solid var(--line);
        padding: 1rem 1.05rem;
        border-radius: 15px;
        box-shadow: 0 7px 22px rgba(38,57,44,.045);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: .79rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--ink);
        letter-spacing: -.035em;
    }

    /* Cards */
    .rm-card {
        background: rgba(255,255,255,.78);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1.05rem 1.15rem;
        box-shadow: 0 8px 24px rgba(38,57,44,.045);
    }

    .rm-report-title {
        font-size: 1.15rem;
        font-weight: 750;
        color: var(--ink);
        margin-bottom: .25rem;
    }

    .rm-note {
        color: var(--muted);
        font-size: .88rem;
    }

    .rm-status {
        padding: .45rem .7rem;
        border-radius: 999px;
        background: #e7f1e9;
        color: #31543b;
        font-weight: 650;
        display: inline-block;
    }

    /* Larger floating action buttons */
    .rm-actions {
        position: sticky;
        bottom: 1rem;
        z-index: 10;
        margin-top: 1rem;
        padding: .55rem;
        border: 1px solid rgba(255,255,255,.9);
        border-radius: 17px;
        background: rgba(255,255,255,.70);
        backdrop-filter: blur(16px) saturate(150%);
        -webkit-backdrop-filter: blur(16px) saturate(150%);
        box-shadow: 0 10px 30px rgba(37,57,44,.10);
    }

    .rm-actions button {
        min-height: 58px !important;
        border-radius: 13px !important;
        font-weight: 650 !important;
        font-size: .88rem !important;
    }

    /* Bigger download / primary buttons */
    .stDownloadButton button,
    button[kind="primary"] {
        min-height: 50px !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }

    /* Inputs */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input {
        border-radius: 11px !important;
    }

    /* Cleaner table */
    [data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--line);
    }

    /* Responsive */
    @media (max-width: 900px) {
        .rm-title { font-size: 1.9rem; }
        .rm-nav-shell + div [data-baseweb="tab"] {
            min-height: 48px;
            padding: 0 .65rem;
            font-size: .78rem;
        }
    }
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
    if "focus_mode" not in st.session_state:
        st.session_state.focus_mode = False


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


def _status_editor(df: pd.DataFrame) -> None:
    st.markdown("### Active / Debarred controls")
    st.caption(
        "Change Active to False to debar a student. "
        "The shortlist updates immediately."
    )

    q = st.text_input(
        "Find a student",
        placeholder="Search by student name or ID",
        key="status_search",
    )

    editable = df[["Student ID", "Name", "Gender", "Grade", "Total", "Active"]].copy()

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
        height=470,
        disabled=["Student ID", "Name", "Gender", "Grade", "Total"],
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

    # Persist only status changes; cleaned values remain untouched.
    status_map = dict(zip(edited["Student ID"], edited["Active"]))
    st.session_state.df.loc[
        st.session_state.df["Student ID"].isin(status_map.keys()), "Active"
    ] = st.session_state.df["Student ID"].map(status_map).fillna(
        st.session_state.df["Active"]
    )


def _render_cleaning_report(report: CleaningReport) -> None:
    st.markdown("### Data Cleaning Report")
    st.caption(
        "A transparent summary of the transformations applied before shortlist filtering."
    )

    rcols = st.columns(5)
    rcols[0].metric("Input rows", f"{report.input_rows:,}")
    rcols[1].metric("Rows removed", f"{report.duplicate_rows_removed:,}")
    rcols[2].metric("Values filled", f"{report.missing_values_filled:,}")
    rcols[3].metric("Score strings parsed", f"{report.score_values_parsed:,}")
    rcols[4].metric("Total corrections", f"{report.total_mismatches_fixed:,}")

    st.markdown(
        """
        <div class="rm-card">
            <div class="rm-report-title">Cleaning logic</div>
            <div class="rm-note">
                Names, gender and grades are normalized; score strings are parsed and
                validated; missing values are handled deterministically; duplicate
                normalized rows are removed conservatively; and Total is recalculated
                from Math + Science + English rather than trusted from the source.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.source_name:
        st.caption(f"Source: {st.session_state.source_name}")


def _render_cleaned_dataset(df: pd.DataFrame, display_cols: list[str]) -> None:
    st.markdown("### Cleaned Dataset")
    st.caption(
        f"{len(df):,} recruitment records after validation and cleaning."
    )

    st.dataframe(
        df[display_cols],
        hide_index=True,
        use_container_width=True,
        height=570,
        column_config={
            "Total": st.column_config.ProgressColumn(
                "Total",
                min_value=0,
                max_value=300,
                format="%d",
            ),
            "Active": st.column_config.CheckboxColumn(
                "Active",
                disabled=True,
            ),
        },
    )

    cleaned_bytes = dataframe_to_csv_bytes(df[display_cols])
    st.download_button(
        "Download cleaned dataset",
        data=cleaned_bytes,
        file_name="dtu_cleaned_student_dataset.csv",
        mime="text/csv",
        type="secondary",
        use_container_width=False,
    )


def _render_shortlist(df: pd.DataFrame, shortlist: pd.DataFrame, min_total: int,
                      grade_filter: list, gender_filter: list, name_filter: str,
                      display_cols: list[str]) -> None:
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
        + (
            " plus selected grade/gender/search filters."
            if (grade_filter or gender_filter or name_filter)
            else "."
        )
    )

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
            "Active": st.column_config.CheckboxColumn(
                "Active",
                disabled=True,
            ),
        },
    )

    export_bytes = dataframe_to_csv_bytes(shortlist[display_cols])

    st.markdown('<div class="rm-actions">', unsafe_allow_html=True)
    action_cols = st.columns([1, 1, 1, 1])

    with action_cols[0]:
        if st.button("View / Filter", use_container_width=True, key="action_view"):
            st.session_state.focus_mode = False
            st.rerun()

    with action_cols[1]:
        if st.button("Search", use_container_width=True, key="action_search"):
            st.session_state["name_filter"] = ""
            st.rerun()

    with action_cols[2]:
        st.download_button(
            "Download dataset",
            data=export_bytes,
            file_name="dtu_shortlist.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
            key="action_download",
        )

    with action_cols[3]:
        if st.button(
            "Exit full screen" if st.session_state.focus_mode else "Full screen",
            use_container_width=True,
            key="action_fullscreen",
        ):
            st.session_state.focus_mode = not st.session_state.focus_mode
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    _init_state()

    # Focus mode hides the sidebar while keeping the dashboard wide.
    if st.session_state.focus_mode:
        st.markdown(
            "<style>[data-testid='stSidebar']{display:none !important;} "
            "[data-testid='stSidebarCollapsedControl']{display:none !important;}</style>",
            unsafe_allow_html=True,
        )

    # Sidebar
    with st.sidebar:
        st.header("1. Load dataset")
        uploaded = st.file_uploader(
            "Upload raw student CSV / Excel",
            type=["csv", "xlsx", "xls"],
            help="CSV is the assessment format; Excel is accepted as a convenience.",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "Process upload",
                use_container_width=True,
                type="primary",
            ) and uploaded:
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

            st.slider(
                "Minimum Total Score",
                min_value=0,
                max_value=max_total,
                value=min(180, max_total),
                step=1,
                key="min_total",
            )

            grade_options = sorted(
                st.session_state.df["Grade"].dropna().astype(int).unique().tolist()
            )
            st.multiselect(
                "Grade",
                options=grade_options,
                placeholder="All grades",
                key="grade_filter",
            )

            st.multiselect(
                "Gender",
                options=sorted(st.session_state.df["Gender"].unique().tolist()),
                placeholder="All genders",
                key="gender_filter",
            )

            st.text_input(
                "Name search",
                placeholder="Type a name...",
                key="name_filter",
            )

    if st.session_state.df is None:
        st.markdown(
            '<div class="rm-kicker">CDIE • Recruitment Manager</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rm-title">Student Data Pipeline</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rm-subtitle">Clean, validate, shortlist, control eligibility, and export recruitment-ready student data.</div>',
            unsafe_allow_html=True,
        )
        st.info("Start by loading the assessment dataset from the sidebar.")
        st.markdown("### What this app demonstrates")
        st.markdown(
            "Automated cleaning • duplicate handling • score parsing • missing-value treatment • "
            "Total recalculation • live shortlisting • eligibility control • CSV export"
        )
        return

    df = st.session_state.df

    min_total = st.session_state.get(
        "min_total", min(180, int(df["Total"].max()))
    )
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
            shortlist["Name"].str.contains(
                name_filter.strip(),
                case=False,
                na=False,
            )
        ]

    # Header
    st.markdown(
        '<div class="rm-kicker">CDIE • Recruitment Manager</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="rm-title">Student Data Pipeline</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="rm-subtitle">Clean, validate, shortlist, control eligibility, and export recruitment-ready student data.</div>',
        unsafe_allow_html=True,
    )

    display_cols = [
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

    # Glass floating navigation. Order intentionally matches assessment request.
    st.markdown('<div class="rm-nav-shell"></div>', unsafe_allow_html=True)
    tab_report, tab_cleaned, tab_status = st.tabs(
        [
            "Data Cleaning Report",
            "Cleaned Dataset",
            "Manage Active / Debarred Students",
        ]
    )

    with tab_report:
        _render_cleaning_report(st.session_state.report)

    with tab_cleaned:
        _render_cleaned_dataset(df, display_cols)

    with tab_status:
        _status_editor(df)

    st.divider()

    # Main shortlist remains visible below the navigation.
    _render_shortlist(
        df,
        shortlist,
        min_total,
        grade_filter,
        gender_filter,
        name_filter,
        display_cols,
    )


if __name__ == "__main__":
    main()
