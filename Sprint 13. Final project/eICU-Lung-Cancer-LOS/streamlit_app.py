"""Interactive visual story for the eICU lung-cancer prolonged-stay project."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from final_visuals import (
    build_all_figures,
    load_project_tables,
    primary_metric_row,
    resolve_paths,
)

st.set_page_config(
    page_title="eICU Prolonged-Stay Prediction",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px;}
    h1, h2, h3 {color: #12355B;}
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #F5F8FC, #FFFFFF);
        border: 1px solid #DDE7F0;
        padding: 14px 16px;
        border-radius: 16px;
        box-shadow: 0 5px 16px rgba(18,53,91,0.07);
    }
    .hero {
        padding: 22px 28px;
        border-radius: 22px;
        background: linear-gradient(120deg, #12355B 0%, #2F80ED 55%, #12A6A6 100%);
        color: white;
        margin-bottom: 18px;
    }
    .hero h1 {color: white; margin: 0 0 8px 0;}
    .hero p {font-size: 1.14rem; margin: 0; opacity: 0.96;}
    .note {
        background: #FFF8EB;
        border-left: 5px solid #F2994A;
        padding: 12px 16px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Can the first 24 hours predict a long ICU stay?</h1>
      <p>Early risk prediction for critically ill lung-cancer patients using the eICU database.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

project_root = Path.cwd()
paths = resolve_paths(project_root=project_root)

try:
    tables = load_project_tables(paths)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info(
        "Run this app from the project root, or edit resolve_paths() in final_visuals.py "
        "to point to your aggregate result folders."
    )
    st.stop()

figures = build_all_figures(tables)
metrics = primary_metric_row(tables["metrics"])

metric_columns = st.columns(5)
metric_columns[0].metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
metric_columns[1].metric("Average precision", f"{metrics['average_precision']:.3f}")
metric_columns[2].metric("Sensitivity", f"{100 * metrics['sensitivity']:.1f}%")
metric_columns[3].metric("Specificity", f"{100 * metrics['specificity']:.1f}%")
metric_columns[4].metric("Low-risk reliability", f"{100 * metrics['negative_predictive_value']:.1f}%")


def show_plotly(fig, key: str) -> None:
    config = {"displaylogo": False, "scrollZoom": False, "toImageButtonOptions": {"format": "png", "scale": 2}}
    try:
        st.plotly_chart(fig, width="stretch", config=config, key=key)
    except TypeError:
        # Compatibility with older Streamlit releases.
        st.plotly_chart(fig, use_container_width=True, config=config, key=key)


story_tab, results_tab, predictors_tab, technical_tab = st.tabs(
    ["📖 The story", "📈 Results", "🫁 What mattered", "🧪 Technical appendix"]
)

with story_tab:
    show_plotly(figures["01_cohort_flow"], "cohort")
    show_plotly(figures["02_prediction_timeline"], "timeline")
    show_plotly(figures["03_feature_coverage"], "coverage")

with results_tab:
    show_plotly(figures["04_model_comparison"], "models")
    show_plotly(figures["05_final_performance_scorecard"], "scorecard")
    left, right = st.columns(2)
    with left:
        show_plotly(figures["06_confusion_matrix"], "confusion")
    with right:
        show_plotly(figures["07_out_of_100_patients"], "waffle")
    if "10_final_roc_pr_curves" in figures:
        show_plotly(figures["10_final_roc_pr_curves"], "curves")
    else:
        st.info("ROC and precision-recall curves appear when the private local test-prediction file is available.")

with predictors_tab:
    show_plotly(figures["08_top_predictors"], "importance")
    st.markdown(
        '<div class="note"><b>Important:</b> These are predictive signals, not proof that a variable causes a longer ICU stay.</div>',
        unsafe_allow_html=True,
    )

with technical_tab:
    show_plotly(figures["09_coefficient_directions"], "coefficients")
    with st.expander("How to explain the main metrics"):
        st.markdown(
            """
            - **ROC-AUC:** how well the model ranks higher-risk patients above lower-risk patients.
            - **Average precision:** how effectively higher-risk predictions concentrate the true long stays.
            - **Sensitivity:** how many real long stays the model catches.
            - **Specificity:** how many shorter stays the model correctly labels as lower risk.
            - **Low-risk reliability (NPV):** when the model says lower risk, how often it is correct.
            """
        )

st.caption(
    "Research demonstration only. The model requires external and prospective validation before any clinical use."
)
