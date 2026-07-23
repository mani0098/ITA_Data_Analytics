"""Create presentation-ready Plotly figures for the eICU lung-cancer project.

The script uses aggregate project outputs and, when available, the private local
final-test prediction file to draw ROC and precision-recall curves.

Examples
--------
From the project root:
    python final_visuals.py

Using a folder containing exported aggregate CSV files:
    python final_visuals.py --data-dir outputs/metrics --qc-dir outputs/cohort/qc

HTML files are always exported. PNG/SVG export is attempted when Kaleido and a
compatible Chrome/Chromium installation are available.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


# -----------------------------------------------------------------------------
# Visual identity
# -----------------------------------------------------------------------------
COLORS = {
    "navy": "#12355B",
    "blue": "#2F80ED",
    "teal": "#12A6A6",
    "cyan": "#56CCF2",
    "green": "#27AE60",
    "orange": "#F2994A",
    "coral": "#EB5757",
    "purple": "#8E5BEF",
    "yellow": "#F2C94C",
    "grey": "#8C98A4",
    "dark": "#1F2937",
    "light": "#F5F8FC",
    "white": "#FFFFFF",
}

SOURCE_COLORS = {
    "APACHE prediction variables": COLORS["purple"],
    "APACHE physiology": COLORS["blue"],
    "APACHE severity": COLORS["navy"],
    "Vital signs": COLORS["teal"],
    "Laboratory": COLORS["orange"],
    "Past history": COLORS["green"],
    "Demographic or admission": COLORS["grey"],
}

FEATURE_LABELS = {
    "apv_ventilated_day1": "Mechanical ventilation (day 1)",
    "vital_periodic_heartrate_max": "Highest heart rate",
    "vital_periodic_sao2_first": "First oxygen saturation",
    "hospitaladmitoffset": "Hospital-to-ICU timing",
    "aps_intubated": "Intubation",
    "history_venous_thromboembolism": "Previous blood clot / PE",
    "vital_periodic_respiration_min": "Lowest respiratory rate",
    "apacheadmissiondx": "Admission diagnosis",
    "aps_ventilated": "Ventilation status",
    "apv_vent_worst_rr_day1": "Ventilated respiratory rate",
    "lab_platelets_max": "Highest platelet count",
    "vital_aperiodic_nibp_systolic_min": "Lowest systolic blood pressure",
    "aps_temperature": "Temperature",
    "aps_glucose": "Glucose",
    "lab_wbc_min": "Lowest white blood cell count",
    "aps_respiratory_rate": "Respiratory rate",
    "history_hypertension": "History of hypertension",
    "history_heart_failure": "History of heart failure",
    "vital_periodic_heartrate_std": "Heart-rate variability",
    "unitvisitnumber": "ICU visit number",
    "apacheadmissiondx_Thoracotomy for lung cancer": "Thoracotomy for lung cancer",
    "unitadmitsource_Recovery Room": "Admission from recovery room",
    "lab_anion_gap_min": "Lowest anion gap",
    "history_home_oxygen": "Home oxygen history",
    "apv_admitsource_2.0": "APACHE admission source",
    "missing__aps_temperature": "Missing APACHE temperature",
    "admissionheight": "Recorded admission height",
    "vital_aperiodic_nibp_mean_median": "Median non-invasive mean BP",
    "apv_diabetes": "Diabetes history",
}

COVERAGE_LABELS = {
    "apv_available": "APACHE admission variables",
    "aps_available": "APACHE physiology",
    "apr_available": "APACHE result / score",
    "lab_any_available": "Laboratory tests",
    "vital_any_available": "Vital signs",
    "history_assessable_by_24h": "Medical history",
}

MODEL_LABELS = {
    "Logistic regression": "Logistic regression",
    "Random forest": "Random forest",
    "Histogram gradient boosting": "Gradient boosting",
    "Dummy classifier": "No-skill reference",
}

FEATURE_SET_LABELS = {
    "Model A: clinical baseline": "Clinical data",
    "Model B: clinical + APACHE": "Clinical + APACHE",
}


@dataclass(frozen=True)
class VisualPaths:
    baseline_summary: Path
    availability: Path
    final_metrics: Path
    bootstrap_ci: Path
    coefficients: Path
    permutation_importance: Path
    test_predictions: Path
    output_dir: Path


def _first_existing(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_paths(
    *,
    project_root: Path | None = None,
    data_dir: Path | None = None,
    qc_dir: Path | None = None,
    output_dir: Path | None = None,
) -> VisualPaths:
    """Resolve project paths while supporting both project and flat-file layouts."""
    root = (project_root or Path.cwd()).resolve()
    metric_dir = data_dir or root / "outputs" / "metrics"
    cohort_qc_dir = qc_dir or root / "outputs" / "cohort" / "qc"
    split_dir = root / "outputs" / "splits"
    figure_dir = output_dir or root / "outputs" / "figures" / "final_storytelling"

    return VisualPaths(
        baseline_summary=_first_existing([
            metric_dir / "baseline_cross_validation_summary.csv",
            root / "baseline_cross_validation_summary.csv",
        ]),
        availability=_first_existing([
            cohort_qc_dir / "modeling_block_availability_v001.csv",
            metric_dir / "modeling_block_availability_v001.csv",
            root / "modeling_block_availability_v001.csv",
        ]),
        final_metrics=_first_existing([
            metric_dir / "final_test_metrics_v001.csv",
            root / "final_test_metrics_v001.csv",
        ]),
        bootstrap_ci=_first_existing([
            metric_dir / "final_test_bootstrap_confidence_intervals.csv",
            root / "final_test_bootstrap_confidence_intervals.csv",
        ]),
        coefficients=_first_existing([
            metric_dir / "final_logistic_coefficient_table.csv",
            root / "final_logistic_coefficient_table.csv",
        ]),
        permutation_importance=_first_existing([
            metric_dir / "final_primary_permutation_importance.csv",
            root / "final_primary_permutation_importance.csv",
        ]),
        test_predictions=_first_existing([
            split_dir / "final_test_predictions_v001.csv",
            data_dir / "final_test_predictions_v001.csv" if data_dir else split_dir / "__missing__.csv",
            root / "final_test_predictions_v001.csv",
        ]),
        output_dir=figure_dir,
    )


def read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return pd.read_csv(path, low_memory=False)


def load_project_tables(paths: VisualPaths) -> dict[str, pd.DataFrame | None]:
    tables: dict[str, pd.DataFrame | None] = {
        "baseline": read_required_csv(paths.baseline_summary, "baseline summary"),
        "availability": read_required_csv(paths.availability, "availability summary"),
        "metrics": read_required_csv(paths.final_metrics, "final test metrics"),
        "bootstrap": read_required_csv(paths.bootstrap_ci, "bootstrap intervals"),
        "coefficients": read_required_csv(paths.coefficients, "coefficient table"),
        "permutation": read_required_csv(paths.permutation_importance, "permutation importance"),
        "predictions": pd.read_csv(paths.test_predictions) if paths.test_predictions.exists() else None,
    }
    return tables


def primary_metric_row(metrics: pd.DataFrame) -> pd.Series:
    mask = metrics["model"].astype(str).str.contains("logistic", case=False, na=False)
    if not mask.any():
        raise ValueError("Primary logistic model row was not found.")
    return metrics.loc[mask].iloc[0]


def friendly_feature_name(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]

    cleaned = feature
    for prefix in ("apv_", "aps_", "apr_", "lab_", "vital_periodic_", "vital_aperiodic_", "history_"):
        cleaned = cleaned.removeprefix(prefix)
    cleaned = re.sub(r"_+", " ", cleaned).strip()
    return cleaned.title()


def apply_presentation_theme(
    fig: go.Figure,
    *,
    title: str,
    subtitle: str | None = None,
    height: int = 760,
    showlegend: bool = True,
) -> go.Figure:
    full_title = title
    if subtitle:
        full_title += f"<br><sup>{subtitle}</sup>"

    fig.update_layout(
        title={"text": full_title, "x": 0.02, "xanchor": "left", "y": 0.97},
        font={"family": "Arial, sans-serif", "size": 17, "color": COLORS["dark"]},
        title_font={"size": 27, "color": COLORS["navy"]},
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        height=height,
        margin={"l": 70, "r": 45, "t": 115, "b": 65},
        showlegend=showlegend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 14},
        },
        hoverlabel={"font_size": 15, "font_family": "Arial"},
    )
    fig.add_annotation(
        text="eICU lung-cancer project • First 24 hours",
        xref="paper",
        yref="paper",
        x=1,
        y=-0.12,
        xanchor="right",
        showarrow=False,
        font={"size": 11, "color": COLORS["grey"]},
    )
    return fig


def build_cohort_flow() -> go.Figure:
    labels = [
        "Eligible lung-cancer<br>ICU stays<br><b>1,860</b>",
        "Stayed ≤24 hours<br><b>471 excluded</b>",
        "24-hour landmark<br>cohort<br><b>1,389</b>",
        "Development set<br><b>1,111</b>",
        "Independent test set<br><b>278</b>",
    ]

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "pad": 30,
                "thickness": 28,
                "line": {"color": COLORS["white"], "width": 2},
                "label": labels,
                "color": [COLORS["blue"], COLORS["grey"], COLORS["teal"], COLORS["navy"], COLORS["orange"]],
                "hovertemplate": "%{label}<extra></extra>",
            },
            link={
                "source": [0, 0, 2, 2],
                "target": [1, 2, 3, 4],
                "value": [471, 1389, 1111, 278],
                "color": ["rgba(140,152,164,0.35)", "rgba(18,166,166,0.30)", "rgba(18,53,91,0.30)", "rgba(242,153,74,0.38)"],
                "hovertemplate": "%{value:,} ICU stays<extra></extra>",
            },
        )
    )
    return apply_presentation_theme(
        fig,
        title="From the source cohort to a fair final test",
        subtitle="Patients had to remain in the ICU beyond 24 hours so all predictors were available before prediction",
        height=720,
        showlegend=False,
    )


def build_prediction_timeline() -> go.Figure:
    fig = go.Figure()
    fig.add_shape(type="line", x0=0, x1=144, y0=0, y1=0, line={"color": COLORS["navy"], "width": 7})
    fig.add_shape(
        type="rect", x0=0, x1=24, y0=-0.18, y1=0.18,
        fillcolor="rgba(47,128,237,0.18)", line={"color": COLORS["blue"], "width": 2},
    )
    points = [
        (0, "ICU admission", COLORS["blue"]),
        (24, "Prediction point", COLORS["teal"]),
        (120, "5-day threshold", COLORS["orange"]),
    ]
    for x, label, color in points:
        fig.add_trace(
            go.Scatter(
                x=[x], y=[0], mode="markers+text", text=[label], textposition="top center",
                marker={"size": 24, "color": color, "line": {"color": COLORS["white"], "width": 3}},
                hovertemplate=f"{label}<extra></extra>", showlegend=False,
            )
        )
    fig.add_annotation(
        x=12, y=-0.42, text="Collect admission data, vital signs,<br>lab tests and medical history",
        showarrow=False, font={"size": 17, "color": COLORS["blue"]},
    )
    fig.add_annotation(
        x=72, y=0.42, text="No information after hour 24<br>was allowed into the model",
        showarrow=False, font={"size": 17, "color": COLORS["dark"]},
    )
    fig.add_annotation(
        x=132, y=-0.40, text="Outcome:<br>ICU stay >5 days?",
        showarrow=False, font={"size": 18, "color": COLORS["orange"]},
    )
    fig.update_xaxes(
        range=[-8, 150], tickvals=[0, 24, 48, 72, 96, 120, 144],
        ticktext=["0 h", "24 h", "2 d", "3 d", "4 d", "5 d", "6 d"],
        title="Time after ICU admission", showgrid=False, zeroline=False,
    )
    fig.update_yaxes(range=[-0.75, 0.75], visible=False)
    return apply_presentation_theme(
        fig,
        title="The prediction was made after the first 24 hours",
        subtitle="A clear timeline prevents future information from leaking into the prediction",
        height=620,
        showlegend=False,
    )


def build_feature_coverage(availability: pd.DataFrame) -> go.Figure:
    plot = availability.copy()
    plot["label"] = plot["feature_block"].map(COVERAGE_LABELS).fillna(plot["feature_block"])
    plot = plot.sort_values("coverage_percent", ascending=True)
    colors = [COLORS["orange"] if value < 95 else COLORS["teal"] for value in plot["coverage_percent"]]

    fig = go.Figure(
        go.Bar(
            x=plot["coverage_percent"], y=plot["label"], orientation="h",
            marker={"color": colors, "line": {"color": COLORS["white"], "width": 1}},
            text=plot["coverage_percent"].map(lambda x: f"{x:.1f}%"),
            textposition="inside", insidetextanchor="end",
            textfont={"size": 16, "color": COLORS["white"]},
            customdata=np.column_stack([plot["available_n"], plot["unavailable_n"]]),
            hovertemplate="%{y}<br>Coverage: %{x:.2f}%<br>Available: %{customdata[0]:,}<br>Missing: %{customdata[1]:,}<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 100], title="Patients with usable data (%)", ticksuffix="%", gridcolor="#E8EEF5")
    fig.update_yaxes(title=None)
    fig.add_vline(x=95, line_dash="dot", line_color=COLORS["grey"], annotation_text="95%", annotation_position="top")
    return apply_presentation_theme(
        fig,
        title="Almost every patient had usable first-day information",
        subtitle="High coverage reduces the number of patients lost because of missing data",
        height=660,
        showlegend=False,
    )


def build_model_comparison(baseline: pd.DataFrame) -> go.Figure:
    plot = baseline.loc[~baseline["model"].eq("Dummy classifier")].copy()
    plot["model_label"] = plot["model"].map(MODEL_LABELS).fillna(plot["model"])
    plot["feature_label"] = plot["feature_set"].map(FEATURE_SET_LABELS).fillna(plot["feature_set"])
    model_order = ["Logistic regression", "Random forest", "Gradient boosting"]
    feature_order = ["Clinical data", "Clinical + APACHE"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Finding long-stay patients", "Separating higher from lower risk"),
        horizontal_spacing=0.13,
    )

    for feature_label, color in zip(feature_order, [COLORS["teal"], COLORS["purple"]]):
        sub = plot.loc[plot["feature_label"].eq(feature_label)].copy()
        sub["order"] = sub["model_label"].map({name: i for i, name in enumerate(model_order)})
        sub = sub.sort_values("order")
        fig.add_trace(
            go.Bar(
                x=sub["model_label"], y=sub["average_precision_mean"], name=feature_label,
                marker_color=color, error_y={"type": "data", "array": sub["average_precision_std"], "visible": True},
                text=sub["average_precision_mean"].map(lambda x: f"{x:.3f}"), textposition="outside",
                hovertemplate="%{x}<br>Average precision: %{y:.3f}<extra></extra>",
                legendgroup=feature_label,
            ), row=1, col=1,
        )
        fig.add_trace(
            go.Bar(
                x=sub["model_label"], y=sub["roc_auc_mean"], name=feature_label,
                marker_color=color, error_y={"type": "data", "array": sub["roc_auc_std"], "visible": True},
                text=sub["roc_auc_mean"].map(lambda x: f"{x:.3f}"), textposition="outside",
                hovertemplate="%{x}<br>ROC-AUC: %{y:.3f}<extra></extra>",
                legendgroup=feature_label, showlegend=False,
            ), row=1, col=2,
        )

    fig.add_hline(y=0.2061, line_dash="dot", line_color=COLORS["grey"], row=1, col=1)
    fig.add_annotation(x=0.02, y=0.2061, xref="x domain", yref="y", text="No-skill ≈ 0.206", showarrow=False, yshift=12, font={"color": COLORS["grey"], "size": 12})
    fig.add_hline(y=0.5, line_dash="dot", line_color=COLORS["grey"], row=1, col=2)
    fig.update_yaxes(title="Average precision", range=[0, 0.52], gridcolor="#E8EEF5", row=1, col=1)
    fig.update_yaxes(title="ROC-AUC", range=[0.45, 0.80], gridcolor="#E8EEF5", row=1, col=2)
    fig.update_xaxes(title=None, tickangle=-15)
    fig.update_layout(barmode="group")
    return apply_presentation_theme(
        fig,
        title="APACHE information improved every real model",
        subtitle="The comparison used five-fold cross-validation on the development set only",
        height=720,
        showlegend=True,
    )


def build_performance_scorecard(metrics: pd.DataFrame) -> go.Figure:
    """Build a spacious 2×3 KPI card layout suitable for slides.

    The earlier bullet-gauge version packed five indicators into one row and
    could overlap during static export. This card layout uses fixed paper
    coordinates and intentionally leaves generous whitespace.
    """
    row = primary_metric_row(metrics)

    cards = [
        {
            "label": "ROC-AUC",
            "value": f"{float(row['roc_auc']):.3f}",
            "caption": "Overall ability to rank higher-risk patients",
            "color": COLORS["blue"],
        },
        {
            "label": "Average precision",
            "value": f"{float(row['average_precision']):.3f}",
            "caption": "Quality of the high-risk ranking",
            "color": COLORS["purple"],
        },
        {
            "label": "Brier score",
            "value": f"{float(row['brier_score']):.3f}",
            "caption": "Probability error — lower is better",
            "color": COLORS["navy"],
        },
        {
            "label": "Long stays detected",
            "value": f"{100 * float(row['sensitivity']):.1f}%",
            "caption": "Sensitivity",
            "color": COLORS["coral"],
        },
        {
            "label": "Short stays recognized",
            "value": f"{100 * float(row['specificity']):.1f}%",
            "caption": "Specificity",
            "color": COLORS["teal"],
        },
        {
            "label": "Low-risk reliability",
            "value": f"{100 * float(row['negative_predictive_value']):.1f}%",
            "caption": "Negative predictive value",
            "color": COLORS["green"],
        },
    ]

    fig = go.Figure()

    # Three equal-width cards per row with ample horizontal and vertical gaps.
    x_positions = [(0.02, 0.34), (0.35, 0.67), (0.68, 1.00)]
    y_positions = [(0.56, 0.93), (0.08, 0.45)]

    for index, card in enumerate(cards):
        row_index = index // 3
        column_index = index % 3
        x0, x1 = x_positions[column_index]
        y0, y1 = y_positions[row_index]
        x_mid = (x0 + x1) / 2

        fig.add_shape(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x0,
            x1=x1,
            y0=y0,
            y1=y1,
            fillcolor=COLORS["white"],
            line={"color": "#DDE7F0", "width": 2},
            layer="below",
        )

        # Colored accent strip.
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x0,
            x1=x1,
            y0=y1 - 0.035,
            y1=y1,
            fillcolor=card["color"],
            line={"width": 0},
            layer="below",
        )

        fig.add_annotation(
            x=x_mid,
            y=y1 - 0.105,
            xref="paper",
            yref="paper",
            text=f"<b>{card['label']}</b>",
            showarrow=False,
            font={"size": 18, "color": COLORS["dark"]},
            align="center",
        )

        fig.add_annotation(
            x=x_mid,
            y=(y0 + y1) / 2,
            xref="paper",
            yref="paper",
            text=f"<b>{card['value']}</b>",
            showarrow=False,
            font={"size": 42, "color": card["color"]},
            align="center",
        )

        fig.add_annotation(
            x=x_mid,
            y=y0 + 0.075,
            xref="paper",
            yref="paper",
            text=card["caption"],
            showarrow=False,
            font={"size": 13, "color": COLORS["grey"]},
            align="center",
        )

    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1])

    return apply_presentation_theme(
        fig,
        title="The model provided a useful — but not perfect — early warning",
        subtitle=(
            f"Independent test set: {int(row['test_n'])} patients • "
            f"{int(row['positive_n'])} stayed in the ICU for more than 5 days"
        ),
        height=790,
        showlegend=False,
    )


def build_confusion_matrix(metrics: pd.DataFrame) -> go.Figure:
    row = primary_metric_row(metrics)
    values = {
        "Correct short stay": int(row["true_negative"]),
        "False alarm": int(row["false_positive"]),
        "Missed long stay": int(row["false_negative"]),
        "Correct long stay": int(row["true_positive"]),
    }
    positions = [
        (0, 1, "Correct short stay", COLORS["blue"]),
        (1, 1, "False alarm", COLORS["orange"]),
        (0, 0, "Missed long stay", COLORS["coral"]),
        (1, 0, "Correct long stay", COLORS["green"]),
    ]
    fig = go.Figure()
    for x, y, label, color in positions:
        fig.add_shape(
            type="rect", x0=x - 0.47, x1=x + 0.47, y0=y - 0.43, y1=y + 0.43,
            fillcolor=color, line={"color": COLORS["white"], "width": 5}, layer="below",
        )
        fig.add_annotation(
            x=x, y=y + 0.08, text=f"<b>{values[label]}</b>", showarrow=False,
            font={"size": 34, "color": COLORS["white"]},
        )
        fig.add_annotation(
            x=x, y=y - 0.18, text=label, showarrow=False,
            font={"size": 16, "color": COLORS["white"]},
        )
    fig.update_xaxes(range=[-0.55, 1.55], tickvals=[0, 1], ticktext=["Predicted ≤5 days", "Predicted >5 days"], side="top", title=None, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-0.55, 1.55], tickvals=[0, 1], ticktext=["Observed >5 days", "Observed ≤5 days"], title=None, showgrid=False, zeroline=False)
    return apply_presentation_theme(
        fig,
        title="The model caught 36 of 57 long stays",
        subtitle=f"Locked probability cut-off: {float(row['threshold']):.3f} • The cut-off was selected before opening the test set",
        height=670,
        showlegend=False,
    )


def build_out_of_100(metrics: pd.DataFrame) -> go.Figure:
    row = primary_metric_row(metrics)
    long_n = int(round(float(row["observed_positive_rate"]) * 100))
    short_n = 100 - long_n
    caught = int(round(long_n * float(row["sensitivity"])))
    missed = long_n - caught
    correct_short = int(round(short_n * float(row["specificity"])))
    false_alarm = short_n - correct_short

    categories = (
        ["Correct short stay"] * correct_short
        + ["False alarm"] * false_alarm
        + ["Missed long stay"] * missed
        + ["Correct long stay"] * caught
    )
    palette = {
        "Correct short stay": COLORS["blue"],
        "False alarm": COLORS["orange"],
        "Missed long stay": COLORS["coral"],
        "Correct long stay": COLORS["green"],
    }
    x = np.tile(np.arange(10), 10)
    y = 9 - np.repeat(np.arange(10), 10)
    fig = go.Figure()
    for category in palette:
        mask = np.array(categories) == category
        fig.add_trace(
            go.Scatter(
                x=x[mask], y=y[mask], mode="markers", name=f"{category} ({int(mask.sum())})",
                marker={"symbol": "square", "size": 30, "color": palette[category], "line": {"color": COLORS["white"], "width": 1.5}},
                hovertemplate=f"{category}<extra></extra>",
            )
        )
    fig.update_xaxes(range=[-0.7, 9.7], visible=False)
    fig.update_yaxes(range=[-0.7, 9.7], visible=False, scaleanchor="x", scaleratio=1)
    fig.add_annotation(
        x=1.03, y=0.60, xref="paper", yref="paper", xanchor="left", showarrow=False,
        text=f"<b>{caught}</b> long stays caught<br><b>{missed}</b> long stays missed<br><b>{false_alarm}</b> false alarms<br><b>{correct_short}</b> short stays correctly identified",
        align="left", font={"size": 18, "color": COLORS["dark"]},
    )
    return apply_presentation_theme(
        fig,
        title="What the result means for 100 similar patients",
        subtitle="Approximate counts based on the independent test-set performance",
        height=720,
        showlegend=True,
    )


def build_top_predictors(permutation: pd.DataFrame, n: int = 12) -> go.Figure:
    plot = permutation.loc[permutation["importance_mean"].gt(0)].head(n).copy()
    plot["friendly"] = plot["feature"].map(friendly_feature_name)
    plot["color"] = plot["source_block"].map(SOURCE_COLORS).fillna(COLORS["grey"])
    plot = plot.sort_values("importance_mean", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=plot["importance_mean"], y=plot["friendly"], orientation="h",
            error_x={"type": "data", "array": plot["importance_std"], "visible": True},
            marker={"color": plot["color"], "line": {"color": COLORS["white"], "width": 1}},
            customdata=np.column_stack([plot["source_block"]]),
            hovertemplate="%{y}<br>Importance: %{x:.4f}<br>%{customdata[0]}<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_xaxes(title="Drop in average precision when the variable was shuffled", gridcolor="#E8EEF5")
    fig.update_yaxes(title=None)

    for source, color in SOURCE_COLORS.items():
        if source in set(plot["source_block"]):
            fig.add_trace(go.Bar(x=[None], y=[None], name=source, marker_color=color, showlegend=True, hoverinfo="skip"))

    return apply_presentation_theme(
        fig,
        title="Breathing support and early instability mattered most",
        subtitle="Permutation importance measures how much performance falls when one variable is randomly shuffled",
        height=760,
        showlegend=True,
    )


def build_coefficient_directions(coefficients: pd.DataFrame, n_each: int = 8) -> go.Figure:
    nonzero = coefficients.loc[coefficients["nonzero"].astype(str).str.lower().isin({"true", "1"})].copy()
    selected = pd.concat([
        nonzero.nsmallest(n_each, "coefficient"),
        nonzero.nlargest(n_each, "coefficient"),
    ]).drop_duplicates("feature")
    selected["friendly"] = selected["feature"].map(friendly_feature_name)
    selected = selected.sort_values("coefficient")
    selected["color"] = np.where(selected["coefficient"].gt(0), COLORS["coral"], COLORS["blue"])

    fig = go.Figure(
        go.Bar(
            x=selected["coefficient"], y=selected["friendly"], orientation="h",
            marker_color=selected["color"],
            customdata=np.column_stack([selected["source_block"]]),
            hovertemplate="%{y}<br>Coefficient: %{x:.3f}<br>%{customdata[0]}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_width=1.5, line_color=COLORS["dark"])
    fig.add_annotation(x=0.98, y=1.05, xref="paper", yref="paper", text="Higher predicted risk →", showarrow=False, font={"color": COLORS["coral"], "size": 15})
    fig.add_annotation(x=0.02, y=1.05, xref="paper", yref="paper", text="← Lower predicted risk", showarrow=False, font={"color": COLORS["blue"], "size": 15})
    fig.update_xaxes(title="Standardized penalized coefficient", gridcolor="#E8EEF5")
    fig.update_yaxes(title=None)
    return apply_presentation_theme(
        fig,
        title="The final model kept only a small set of useful signals",
        subtitle="Predictive associations only — they do not prove cause and effect",
        height=790,
        showlegend=False,
    )


def build_roc_pr_curves(predictions: pd.DataFrame) -> go.Figure:
    required = {"observed_outcome", "primary_probability", "secondary_probability"}
    missing = required.difference(predictions.columns)
    if missing:
        raise KeyError(f"Test prediction file is missing columns: {sorted(missing)}")

    y = predictions["observed_outcome"].astype(int).to_numpy()
    series = {
        "Calibrated logistic regression": predictions["primary_probability"].to_numpy(),
        "Calibrated random forest": predictions["secondary_probability"].to_numpy(),
    }
    fig = make_subplots(rows=1, cols=2, subplot_titles=("ROC curve", "Precision–recall curve"), horizontal_spacing=0.14)
    for (label, probability), color in zip(series.items(), [COLORS["blue"], COLORS["purple"]]):
        fpr, tpr, _ = roc_curve(y, probability)
        precision, recall, _ = precision_recall_curve(y, probability)
        auc = roc_auc_score(y, probability)
        ap = average_precision_score(y, probability)
        fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", line={"color": color, "width": 3}, name=f"{label} (AUC {auc:.3f})", legendgroup=label), row=1, col=1)
        fig.add_trace(go.Scatter(x=recall, y=precision, mode="lines", line={"color": color, "width": 3}, name=f"{label} (AP {ap:.3f})", legendgroup=label, showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line={"color": COLORS["grey"], "dash": "dot"}, name="No discrimination", showlegend=True), row=1, col=1)
    prevalence = y.mean()
    fig.add_trace(go.Scatter(x=[0, 1], y=[prevalence, prevalence], mode="lines", line={"color": COLORS["grey"], "dash": "dot"}, name=f"Prevalence ({prevalence:.3f})", showlegend=True), row=1, col=2)
    fig.update_xaxes(title="False-positive rate", range=[0, 1], gridcolor="#E8EEF5", row=1, col=1)
    fig.update_yaxes(title="Sensitivity", range=[0, 1], gridcolor="#E8EEF5", row=1, col=1)
    fig.update_xaxes(title="Sensitivity / recall", range=[0, 1], gridcolor="#E8EEF5", row=1, col=2)
    fig.update_yaxes(title="Precision", range=[0, 1], gridcolor="#E8EEF5", row=1, col=2)
    return apply_presentation_theme(
        fig,
        title="Both final models separated risk moderately well",
        subtitle="Independent test-set curves; the logistic model remained primary because it was more interpretable and had higher average precision",
        height=700,
        showlegend=True,
    )


def build_all_figures(tables: dict[str, pd.DataFrame | None]) -> dict[str, go.Figure]:
    figures: dict[str, go.Figure] = {
        "01_cohort_flow": build_cohort_flow(),
        "02_prediction_timeline": build_prediction_timeline(),
        "03_feature_coverage": build_feature_coverage(tables["availability"]),  # type: ignore[arg-type]
        "04_model_comparison": build_model_comparison(tables["baseline"]),  # type: ignore[arg-type]
        "05_final_performance_scorecard": build_performance_scorecard(tables["metrics"]),  # type: ignore[arg-type]
        "06_confusion_matrix": build_confusion_matrix(tables["metrics"]),  # type: ignore[arg-type]
        "07_out_of_100_patients": build_out_of_100(tables["metrics"]),  # type: ignore[arg-type]
        "08_top_predictors": build_top_predictors(tables["permutation"]),  # type: ignore[arg-type]
        "09_coefficient_directions": build_coefficient_directions(tables["coefficients"]),  # type: ignore[arg-type]
    }
    predictions = tables.get("predictions")
    if isinstance(predictions, pd.DataFrame):
        figures["10_final_roc_pr_curves"] = build_roc_pr_curves(predictions)
    return figures


def export_figures(
    figures: dict[str, go.Figure],
    output_dir: Path,
    *,
    static: bool = True,
    width: int = 1600,
    height: int = 900,
    scale: float = 2.0,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    static_error_reported = False
    for name, fig in figures.items():
        html_path = output_dir / f"{name}.html"
        fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)
        print(f"HTML: {html_path}")

        if not static:
            continue

        for extension in ("png", "svg"):
            path = output_dir / f"{name}.{extension}"
            try:
                fig.write_image(path, width=width, height=height, scale=scale)
                print(f"{extension.upper()}: {path}")
            except Exception as exc:  # Plotly/Kaleido/Chrome errors vary by platform.
                if not static_error_reported:
                    print("\nStatic export was skipped because Kaleido/Chrome is not ready.")
                    print("Install or upgrade Kaleido, then ensure Chrome/Chromium is available.")
                    print(f"First export error: {exc}\n")
                    static_error_reported = True
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate final Plotly storytelling figures.")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None, help="Folder containing metric CSV files.")
    parser.add_argument("--qc-dir", type=Path, default=None, help="Folder containing modeling_block_availability_v001.csv.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-static", action="store_true", help="Export HTML only.")
    parser.add_argument("--show", action="store_true", help="Open figures in the configured Plotly renderer.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = resolve_paths(
        project_root=args.project_root,
        data_dir=args.data_dir,
        qc_dir=args.qc_dir,
        output_dir=args.output_dir,
    )
    tables = load_project_tables(paths)
    figures = build_all_figures(tables)
    export_figures(figures, paths.output_dir, static=not args.no_static)
    if args.show:
        for figure in figures.values():
            figure.show()
    print(f"\nCreated {len(figures)} presentation-ready figures in: {paths.output_dir}")
    if tables["predictions"] is None:
        print("ROC/PR curves were skipped because the private test prediction file was not found.")


if __name__ == "__main__":
    main()


from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# Presentation styling
# ============================================================

MODEL_ORDER = [
    "Logistic Regression",
    "Random Forest",
]

MODEL_COLORS = {
    "Logistic Regression": "#18A3A5",  # teal, matching the current Slide 11
    "Random Forest": "#8754E8",        # purple, matching the current Slide 11
}

NAVY = "#123A70"
TEXT_COLOR = "#172234"
MUTED_COLOR = "#718096"
GRID_COLOR = "#DCE6F2"

OUTCOME_PREVALENCE = 0.206121

# Brier score of a model that predicts only the outcome prevalence.
PREVALENCE_ONLY_BRIER = (
    OUTCOME_PREVALENCE
    * (1 - OUTCOME_PREVALENCE)
)


METRICS = [
    {
        "column": "average_precision",
        "panel_title": "Finding long-stay patients",
        "axis_title": "Average precision",
        "range": [0.19, 0.44],
        "higher_is_better": True,
        "reference_value": OUTCOME_PREVALENCE,
        "reference_label": "No-skill = 0.206",
    },
    {
        "column": "roc_auc",
        "panel_title": "Separating higher from lower risk",
        "axis_title": "ROC-AUC",
        "range": [0.45, 0.75],
        "higher_is_better": True,
        "reference_value": 0.50,
        "reference_label": "No discrimination = 0.500",
    },
    {
        "column": "brier_score",
        "panel_title": "Quality of predicted probabilities",
        "axis_title": "Brier score",
        "range": [0.14, 0.22],
        "higher_is_better": False,
        "reference_value": PREVALENCE_ONLY_BRIER,
        "reference_label": (
            f"Prevalence-only = {PREVALENCE_ONLY_BRIER:.3f}"
        ),
    },
]


# ============================================================
# Data preparation
# ============================================================

def _standardize_model_name(value: str) -> str:
    """
    Convert the model names used in the CSV files into short,
    presentation-friendly names.
    """
    value_lower = str(value).strip().lower()

    if "logistic" in value_lower:
        return "Logistic Regression"

    if "random forest" in value_lower:
        return "Random Forest"

    return str(value).strip()


def _check_required_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    file_description: str,
) -> None:
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{file_description} is missing the following columns: "
            f"{sorted(missing_columns)}"
        )


def _validate_two_models(
    df: pd.DataFrame,
    source_description: str,
) -> pd.DataFrame:
    """
    Keep and order only Logistic Regression and Random Forest.
    """
    df = df.copy()

    df["display_model"] = (
        df["model"]
        .map(_standardize_model_name)
    )

    df = df[
        df["display_model"].isin(MODEL_ORDER)
    ].copy()

    missing_models = (
        set(MODEL_ORDER)
        - set(df["display_model"])
    )

    if missing_models:
        raise ValueError(
            f"{source_description} does not contain: "
            f"{sorted(missing_models)}"
        )

    duplicated_models = df[
        "display_model"
    ].duplicated(keep=False)

    if duplicated_models.any():
        duplicates = df.loc[
            duplicated_models,
            "display_model",
        ].tolist()

        raise ValueError(
            f"{source_description} contains duplicate rows "
            f"for these models: {duplicates}"
        )

    return (
        df.set_index("display_model")
        .loc[MODEL_ORDER]
        .reset_index()
    )


def load_before_after_model_metrics(
    baseline_summary_csv: str | Path,
    calibration_comparison_csv: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the matched model-comparison data.

    Before:
        Baseline five-fold cross-validation results using
        Model B: clinical + APACHE.

    After:
        Tuned and sigmoid-calibrated development
        out-of-fold results.
    """
    baseline_df = pd.read_csv(
        baseline_summary_csv
    )

    calibrated_df = pd.read_csv(
        calibration_comparison_csv
    )

    baseline_required = {
        "feature_set",
        "model",
        "average_precision_mean",
        "roc_auc_mean",
        "brier_score_mean",
    }

    calibrated_required = {
        "model",
        "calibration_status",
        "average_precision",
        "roc_auc",
        "brier_score",
    }

    _check_required_columns(
        baseline_df,
        baseline_required,
        "Baseline summary CSV",
    )

    _check_required_columns(
        calibrated_df,
        calibrated_required,
        "Calibration comparison CSV",
    )

    # --------------------------------------------------------
    # BEFORE: use Model B only
    # --------------------------------------------------------

    before_df = baseline_df[
        baseline_df["feature_set"]
        .astype(str)
        .str.contains(
            r"clinical \+ APACHE",
            case=False,
            regex=True,
        )
    ].copy()

    before_df = before_df.rename(
        columns={
            "average_precision_mean":
                "average_precision",
            "roc_auc_mean":
                "roc_auc",
            "brier_score_mean":
                "brier_score",
        }
    )

    before_df = _validate_two_models(
        before_df,
        "Baseline Model B results",
    )

    # --------------------------------------------------------
    # AFTER: use the calibrated finalist models
    # --------------------------------------------------------

    after_df = calibrated_df[
        calibrated_df["calibration_status"]
        .astype(str)
        .str.contains(
            "sigmoid calibrated",
            case=False,
            regex=False,
        )
    ].copy()

    after_df = _validate_two_models(
        after_df,
        "Calibrated development results",
    )

    return before_df, after_df


# ============================================================
# Figure creation
# ============================================================

def _metric_winner(
    df: pd.DataFrame,
    metric_column: str,
    higher_is_better: bool,
) -> str:
    values = df.set_index(
        "display_model"
    )[metric_column]

    if higher_is_better:
        return values.idxmax()

    return values.idxmin()


def _wrap_main_title(title: str) -> str:
    """
    Force long slide-style titles onto two lines
    so they do not get cropped in Plotly exports.
    """
    title = title.strip()

    replacements = {
        "Before tuning, Random Forest led the finalist comparison":
            "Before tuning,<br>Random Forest led the finalist comparison",

        "After tuning and calibration, Logistic Regression offered the better overall trade-off":
            "After tuning and calibration,<br>Logistic Regression offered the better overall trade-off",
    }

    return replacements.get(title, title)


def create_model_stage_figure(
    metrics_df: pd.DataFrame,
    title: str,
    subtitle: str,
    footer_message: str,
    output_png: str | Path,
    output_svg: str | Path | None = None,
    output_html: str | Path | None = None,
) -> go.Figure:
    """
    Create one 16:9 presentation figure.

    The exact same function is used for the before and after
    figures, ensuring identical visual structure.
    """
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[
            metric["panel_title"]
            for metric in METRICS
        ],
        horizontal_spacing=0.075,
    )

    for panel_number, metric in enumerate(
        METRICS,
        start=1,
    ):
        metric_column = metric["column"]

        winner = _metric_winner(
            metrics_df,
            metric_column,
            metric["higher_is_better"],
        )

        for model_name in MODEL_ORDER:
            model_row = metrics_df.loc[
                metrics_df["display_model"]
                == model_name
            ].iloc[0]

            metric_value = float(
                model_row[metric_column]
            )

            fig.add_trace(
                go.Bar(
                    x=[model_name],
                    y=[metric_value],
                    name=model_name,
                    legendgroup=model_name,
                    showlegend=(
                        panel_number == 1
                    ),
                    marker={
                        "color":
                            MODEL_COLORS[model_name],
                        "line": {
                            "color": (
                                NAVY
                                if model_name == winner
                                else MODEL_COLORS[
                                    model_name
                                ]
                            ),
                            "width": (
                                3
                                if model_name == winner
                                else 0
                            ),
                        },
                    },
                    text=[
                        f"{metric_value:.3f}"
                    ],
                    textposition="outside",
                    textfont={
                        "size": 18,
                        "color": TEXT_COLOR,
                    },
                    cliponaxis=False,
                    hovertemplate=(
                        f"<b>{model_name}</b>"
                        f"<br>{metric['axis_title']}: "
                        "%{y:.3f}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=panel_number,
            )

        # Reference line
        fig.add_hline(
            y=metric["reference_value"],
            line_dash="dot",
            line_width=2,
            line_color="#8B98A8",
            row=1,
            col=panel_number,
        )

        # Reference line label
        x_reference = (
            "x domain"
            if panel_number == 1
            else f"x{panel_number} domain"
        )

        y_reference = (
            "y"
            if panel_number == 1
            else f"y{panel_number}"
        )

        fig.add_annotation(
            x=0.02,
            y=metric["reference_value"],
            xref=x_reference,
            yref=y_reference,
            text=metric["reference_label"],
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font={
                "size": 12,
                "color": MUTED_COLOR,
            },
        )

        direction_text = (
            "Higher is better"
            if metric["higher_is_better"]
            else "Lower is better"
        )

        fig.add_annotation(
            x=0.5,
            y=1.055,
            xref=(
                "x domain"
                if panel_number == 1
                else f"x{panel_number} domain"
            ),
            yref=(
                "y domain"
                if panel_number == 1
                else f"y{panel_number} domain"
            ),
            text=direction_text,
            showarrow=False,
            font={
                "size": 12,
                "color": MUTED_COLOR,
            },
        )

        fig.update_yaxes(
            title_text=metric["axis_title"],
            range=metric["range"],
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=1,
            zeroline=False,
            tickfont={
                "size": 14,
                "color": TEXT_COLOR,
            },
            title_font={
                "size": 18,
                "color": TEXT_COLOR,
            },
            row=1,
            col=panel_number,
        )

        fig.update_xaxes(
            title_text="",
            categoryorder="array",
            categoryarray=MODEL_ORDER,
            tickangle=-12,
            tickfont={
                "size": 15,
                "color": TEXT_COLOR,
            },
            showgrid=False,
            row=1,
            col=panel_number,
        )

        fig.update_layout(
            template="plotly_white",
            width=1600,
            height=900,
            barmode="group",
            bargap=0.28,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin={
                "l": 60,
                "r": 45,
                "t": 25,
                "b": 25,
            },
            font={
                "family": "Arial",
                "color": TEXT_COLOR,
            },
            legend={
                "orientation": "h",
                "x": 0.99,
                "xanchor": "right",
                "y": 0.865,
                "yanchor": "middle",
                "font": {
                    "size": 15,
                    "color": TEXT_COLOR,
                },
                "title": {
                    "text": "",
                },
            },
            uniformtext={
                "minsize": 13,
                "mode": "hide",
            },
        )

        for panel_number in range(1, 4):
            fig.update_yaxes(
                domain=[0.12, 0.69],
                row=1,
                col=panel_number,
            )


        fig.add_annotation(
        x=0.01,
        y=0.985,
        xref="paper",
        yref="paper",
        text=f"<b>{title}</b>",
        showarrow=False,
        xanchor="left",
        yanchor="top",
        align="left",
        font={
            "family": "Arial",
            "size": 29,
            "color": NAVY,
        },
    )

    fig.add_annotation(
        x=0.01,
        y=0.925,
        xref="paper",
        yref="paper",
        text=subtitle,
        showarrow=False,
        xanchor="left",
        yanchor="top",
        align="left",
        font={
            "family": "Arial",
            "size": 18,
            "color": NAVY,
        },
    )


    # Format the panel titles.
    panel_titles = {
        metric["panel_title"]
        for metric in METRICS
    }

    for annotation in fig.layout.annotations:
        if annotation.text in panel_titles:
            annotation.font = {
                "size": 17,
                "color": TEXT_COLOR,
            }

            annotation.y = 0.755
            annotation.yref = "paper"

    fig.add_annotation(
        x=0.5,
        y=0.025,
        xref="paper",
        yref="paper",
        text=footer_message,
        showarrow=False,
        align="center",
        font={
            "size": 15,
            "color": MUTED_COLOR,
        },
    )

    output_png = Path(output_png)

    output_png.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.write_image(
        output_png,
        scale=2,
    )

    if output_svg is not None:
        output_svg = Path(output_svg)

        output_svg.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fig.write_image(
            output_svg,
        )

    if output_html is not None:
        output_html = Path(output_html)

        output_html.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fig.write_html(
            output_html,
            include_plotlyjs="cdn",
        )

    return fig


def create_before_after_model_comparison_figures(
    baseline_summary_csv: str | Path,
    calibration_comparison_csv: str | Path,
    output_directory: str | Path,
) -> dict[str, Path]:
    """
    Generate two perfectly matched presentation figures:

    1. Before tuning.
    2. After tuning and calibration.
    """
    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    before_df, after_df = (
        load_before_after_model_metrics(
            baseline_summary_csv=
                baseline_summary_csv,
            calibration_comparison_csv=
                calibration_comparison_csv,
        )
    )

    before_png = (
        output_directory
        / "04a_before_tuning_model_comparison.png"
    )

    before_svg = (
        output_directory
        / "04a_before_tuning_model_comparison.svg"
    )

    before_html = (
        output_directory
        / "04a_before_tuning_model_comparison.html"
    )

    after_png = (
        output_directory
        / "04b_after_tuning_and_calibration.png"
    )

    after_svg = (
        output_directory
        / "04b_after_tuning_and_calibration.svg"
    )

    after_html = (
        output_directory
        / "04b_after_tuning_and_calibration.html"
    )

    create_model_stage_figure(
        metrics_df=before_df,
        title=(
            "Before tuning, "
            "Random Forest looked better"
        ),
        subtitle=(
            "Baseline five-fold cross-validation using "
            "clinical + APACHE information"
        ),
        footer_message=(
            "Random Forest started ahead in ranking "
            "and probability quality."
        ),
        output_png=before_png,
        output_svg=before_svg,
        output_html=before_html,
    )

    create_model_stage_figure(
        metrics_df=after_df,
        title=(
            "After tuning and calibration, "
            "Logistic Regression offered the better overall trade-off"
        ),
        subtitle=(
            "Development out-of-fold results after hyperparameter "
            "tuning and sigmoid calibration"
        ),
        footer_message=(
            "Logistic Regression had higher average precision, "
            "virtually identical ROC-AUC, a slightly lower "
            "Brier score, and much greater interpretability."
        ),
        output_png=after_png,
        output_svg=after_svg,
        output_html=after_html,
    )

    return {
        "before_png": before_png,
        "before_svg": before_svg,
        "before_html": before_html,
        "after_png": after_png,
        "after_svg": after_svg,
        "after_html": after_html,
    }