from __future__ import annotations

from typing import Iterable

import streamlit as st


def render_chart(figure, **kwargs) -> None:
    figure.update_layout(
        template="plotly_white",
        font={"family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", "color": "#344054"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"bgcolor": "#ffffff", "font": {"color": "#172033"}},
    )
    st.plotly_chart(figure, width="stretch", **kwargs)


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


def format_percent(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def kpi_card(label: str, value: str, help_text: str = "", accent: str = "navy") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {accent}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(metrics: Iterable[tuple[str, str, str, str]], columns: int = 4) -> None:
    items = list(metrics)
    for start in range(0, len(items), columns):
        row = st.columns(columns)
        for col, (label, value, help_text, accent) in zip(row, items[start:start + columns]):
            with col:
                kpi_card(label, value, help_text, accent)


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #172033;
            --muted: #657187;
            --line: #e4e8f0;
            --paper: #ffffff;
            --canvas: #f5f7fb;
            --primary: #5146d8;
            --green: #16836d;
            --amber: #a96512;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--canvas);
            color: var(--ink);
        }
        html, body, [class*="css"] {
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        header[data-testid="stHeader"] {
            background: rgba(245, 247, 251, .96);
            border-bottom: 1px solid var(--line);
        }
        [data-testid="stToolbar"] { color: var(--ink); }
        .block-container {
            max-width: 1320px;
            padding-top: 1.35rem;
            padding-bottom: 2.75rem;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.1rem;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #56647a;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            min-height: 44px;
            margin: 4px 4px;
            padding: 9px 11px;
            border: 1px solid transparent;
            border-radius: 9px;
            color: #526077;
            font-size: 0.9rem;
            font-weight: 500;
            transition: background .15s ease, border-color .15s ease;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: #f0efff;
            border-color: #e3e1ff;
            color: #4037a8;
            font-weight: 600;
        }
        [data-testid="stSidebar"] input[type="radio"] { accent-color: var(--primary); }
        [data-testid="stSidebar"] [data-testid="stRadio"] div {
            gap: 0.15rem;
        }
        h1 {
            color: #172033 !important;
            font-size: 1.78rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.04em;
            line-height: 1.2 !important;
            margin-bottom: 0.25rem !important;
        }
        h2, h3 {
            color: #202b40 !important;
            letter-spacing: -0.02em;
        }
        h2 {
            font-size: 1.18rem !important;
            font-weight: 650 !important;
        }
        h3 {
            font-size: 1.08rem !important;
            font-weight: 650 !important;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {
            color: #344054;
        }
        [data-testid="stCaptionContainer"] {
            color: #5c687d !important;
            margin-bottom: 1.1rem;
        }
        .kpi-card {
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 11px;
            padding: 15px 16px;
            min-height: 108px;
            box-shadow: 0 3px 12px rgba(27, 39, 67, .035);
        }
        .kpi-card.green { border-top: 3px solid var(--green); }
        .kpi-card.amber { border-top: 3px solid var(--amber); }
        .kpi-card.red { border-top: 3px solid #ba3f46; }
        .kpi-card.navy { border-top: 3px solid var(--primary); }
        .kpi-label {
            color: #59667b;
            font-size: .7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .035em;
        }
        .kpi-value {
            color: var(--ink);
            font-size: 1.48rem;
            line-height: 1.2;
            font-weight: 700;
            margin-top: 8px;
        }
        .kpi-help {
            color: #5e6a7e;
            font-size: .72rem;
            margin-top: 7px;
            min-height: 16px;
        }
        .insight {
            background: #f0efff;
            border: 1px solid #e2e0ff;
            border-radius: 10px;
            padding: 13px 15px;
            color: #38385f;
            line-height: 1.55;
        }
        .insight b { color: #25234d; }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
            background: #ffffff;
        }
        [data-testid="stPlotlyChart"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 11px;
            padding: 6px;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 10px;
        }
        [data-testid="stAlert"] {
            border-radius: 10px;
        }
        .stButton button {
            border-radius: 8px;
            border: 1px solid #dce1ea;
            color: #344054;
            background: #ffffff;
            font-weight: 600;
        }
        .stButton button:hover {
            border-color: #b8b2f3;
            color: #4037a8;
        }
        .stNumberInput input, .stTextInput input {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
