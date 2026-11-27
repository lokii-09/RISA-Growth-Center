from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics.metrics import calculate_all_kpis
from src.assistant.engine import answer_question, configured_provider
from src.assistant.proposals import (
    apply_confirmed_proposal,
    is_explicit_proposal_confirmation,
)
from src.assistant.tools import build_context
from src.cleaning import clean_dataset
from src.dashboard.components import apply_page_style, format_inr, format_percent, kpi_card, metric_grid, render_chart
from src.dashboard.scenario import ScenarioInputs, calculate_scenario
from src.dashboard.state import (
    apply_campaign_spend_edits,
    effective_budget,
    initialize_state,
    reset_budget_state,
    set_campaign_spend,
    set_total_budget,
)
from src.ingestion import load_workbook


PROJECT_ROOT = Path(__file__).resolve().parent
WORKBOOK = PROJECT_ROOT / "data" / "Attendee Dataset.xlsx"


@st.cache_resource
def load_phase0():
    return clean_dataset(load_workbook(WORKBOOK))


@st.cache_data
def load_kpis():
    return calculate_all_kpis(load_phase0())


def historical_label() -> None:
    st.caption("Historical source | Calculated from the immutable workbook through Phase 0")


def initial_scenario_assumptions(kpis: dict[str, object]) -> dict[str, object]:
    baseline = kpis["baseline"]
    return {
        "visitor_target": 2200,
        "registration_conversion": (
            baseline.external_registrations / baseline.identified_external_people
            if baseline.identified_external_people else 0.0
        ),
        "confirmation_rate": (
            baseline.confirmed_external_registrations / baseline.external_registrations
            if baseline.external_registrations else 0.0
        ),
        "show_up_rate": float(kpis["registered_show_rate"]),
        "walk_ins": baseline.walk_in_attendees,
        "marketing_budget": float(baseline.revised_budget),
    }


def command_center(kpis: dict[str, object]) -> None:
    st.title("Command Center")
    historical_label()

    baseline = kpis["baseline"]
    target = baseline.confirmed_external_registrations
    revised_target = load_phase0().working["Targets"].sort_values("effective_at").iloc[-1]
    attendee_target = int(revised_target["unique_external_visitors_goal"])
    achievement = baseline.unique_external_attendees / attendee_target if attendee_target else 0

    metric_grid([
        ("Unique external attendees", f"{baseline.unique_external_attendees:,}", f"{format_percent(achievement)} of visitor target", "navy"),
        ("External registrations", f"{baseline.external_registrations:,}", "Unique registration IDs", "navy"),
        ("Confirmed registrations", f"{baseline.confirmed_external_registrations:,}", "Latest confirmed status", "green"),
        ("Registered show-up rate", format_percent(kpis["registered_show_rate"]), "1925 registered attendees / 2500 confirmed", "green"),
        ("Registered attendees", f"{baseline.registered_attendees:,}", "Verified attendance with registration", "green"),
        ("Walk-in attendees", f"{baseline.walk_in_attendees:,}", "Verified external attendance without registration", "amber"),
        ("Marketing spend", format_inr(baseline.campaign_spend), "Posted by event close", "navy"),
        ("Budget remaining", format_inr(baseline.budget_remaining), "₹300,000 revised budget", "amber"),
        ("Blended cost per attendee", format_inr(kpis["blended_cost_per_attendee"]), "Spend / all external attendees", "navy"),
    ], 3)

    st.divider()
    left, right = st.columns((1.25, 1))
    with left:
        st.subheader("Attendee growth funnel")
        funnel = kpis["funnel"]
        stages = [
            ("Identified visitors", funnel["identified_page_visitors"]),
            ("Registration starters", funnel["registration_starters"]),
            ("Completed registrations", funnel["external_registrations"]),
            ("Confirmed registrations", funnel["confirmed_external_registrations"]),
            ("Registered attendees", funnel["registered_attendees"]),
        ]
        fig = go.Figure(go.Funnel(
            y=[name for name, _ in stages],
            x=[value for _, value in stages],
            textinfo="value+percent initial",
            marker={"color": ["#315bcb", "#5579d5", "#7a98df", "#198754", "#7bc6a4"]},
        ))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=360)
        render_chart(fig)

    with right:
        st.subheader("Attendance versus target")
        fig = go.Figure(go.Bar(
            x=["Visitor target", "Unique attendees"],
            y=[attendee_target, baseline.unique_external_attendees],
            marker_color=["#d9e2f2", "#315bcb"],
            text=[attendee_target, baseline.unique_external_attendees],
            textposition="outside",
        ))
        fig.update_layout(yaxis_title="Unique external people", margin=dict(l=20, r=20, t=20, b=20), height=360)
        render_chart(fig)

    col1, col2 = st.columns((1, 1))
    with col1:
        st.subheader("Budget utilization")
        utilization = baseline.campaign_spend / baseline.revised_budget if baseline.revised_budget else 0
        fig = go.Figure(go.Pie(
            labels=["Spent", "Remaining"],
            values=[baseline.campaign_spend, max(baseline.budget_remaining, 0)],
            hole=.72,
            marker={"colors": ["#315bcb", "#dde5f2"]},
            textinfo="label+percent",
        ))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300,
                          annotations=[dict(text=f"{format_percent(utilization)}", x=.5, y=.5, showarrow=False)])
        render_chart(fig)

    with col2:
        st.subheader("Attendance by day")
        attendance = kpis["attendance_by_day"]
        day_frame = pd.DataFrame({
            "Day": [pd.Timestamp(day).strftime("%d %b") for day in attendance],
            "Unique attendees": list(attendance.values()),
        })
        fig = px.bar(day_frame, x="Day", y="Unique attendees", text="Unique attendees",
                     color_discrete_sequence=["#315bcb"])
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        render_chart(fig)

    st.subheader("Campaign summary")
    campaigns = kpis["campaigns"].sort_values("attributed_attendees", ascending=False)
    display = campaigns[["campaign_name", "spend", "external_registrations", "confirmed_external_registrations",
                         "attributed_attendees", "cost_per_attendee"]].copy()
    display.columns = ["Campaign", "Spend", "Registrations", "Confirmed", "Attendees", "Cost / attendee"]
    st.dataframe(display, width="stretch", hide_index=True,
                 column_config={
                     "Spend": st.column_config.NumberColumn(format="₹%.0f"),
                     "Cost / attendee": st.column_config.NumberColumn(format="₹%.2f"),
                 })

    st.subheader("Important indicators")
    largest = campaigns.iloc[0]
    weakest = campaigns.sort_values("confirmed_to_attended").iloc[0]
    st.markdown(
        f'<div class="insight"><b>Largest attributed volume:</b> {largest["campaign_name"]} delivered '
        f'{int(largest["attributed_attendees"]):,} attendees attributed through the recorded campaign source. '
        f'<b>Review first:</b> {weakest["campaign_name"]} has the lowest confirmed-to-attended rate at '
        f'{format_percent(float(weakest["confirmed_to_attended"]))}. '
        f'These are historical recorded relationships, not proof of causal impact.</div>',
        unsafe_allow_html=True,
    )


def funnel_analysis(kpis: dict[str, object]) -> None:
    st.title("Funnel Analysis")
    historical_label()
    funnel = kpis["funnel"]
    stages = [
        ("Identified visitors", funnel["identified_page_visitors"]),
        ("Registration starters", funnel["registration_starters"]),
        ("Completed registrations", funnel["external_registrations"]),
        ("Confirmed registrations", funnel["confirmed_external_registrations"]),
        ("Registered attendees", funnel["registered_attendees"]),
    ]

    rows = []
    for index, (name, count) in enumerate(stages):
        if index == 0:
            previous = None
            dropoff = 0
            dropoff_pct = 0.0
            conversion = 100.0
        else:
            previous = stages[index - 1][1]
            dropoff = max(previous - count, 0)
            dropoff_pct = dropoff / previous * 100 if previous else 0
            conversion = count / previous * 100 if previous else 0
        rows.append({
            "Stage": name,
            "Count": count,
            "Conversion": conversion,
            "Drop-off": dropoff,
            "Drop-off %": dropoff_pct,
        })

    fig = go.Figure(go.Funnel(
        y=[row["Stage"] for row in rows],
        x=[row["Count"] for row in rows],
        texttemplate="%{value:,}",
        marker={"color": ["#315bcb", "#5579d5", "#7a98df", "#198754", "#7bc6a4"]},
    ))
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=420)
    render_chart(fig)

    table = pd.DataFrame(rows)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Conversion": st.column_config.NumberColumn(format="%.1f%%"),
            "Drop-off %": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    bottleneck = max(rows[1:], key=lambda row: row["Drop-off"])
    st.markdown(
        f'<div class="insight"><b>Largest bottleneck:</b> {bottleneck["Stage"]} follows '
        f'{bottleneck["Drop-off"]:,} people lost from the previous stage '
        f'({bottleneck["Drop-off %"]:.1f}%). Registered show-up must be read separately from walk-ins.</div>',
        unsafe_allow_html=True,
    )


def campaign_performance(kpis: dict[str, object]) -> None:
    st.title("Campaign Performance")
    historical_label()
    frame = kpis["campaigns"].copy()

    campaign_names = st.multiselect(
        "Campaign filter",
        frame["campaign_name"].sort_values().tolist(),
        default=[],
    )
    if campaign_names:
        frame = frame[frame["campaign_name"].isin(campaign_names)]

    if frame.empty:
        st.info("No campaigns match the selected filter.")
        return

    frame["registration_rate"] = frame["external_registrations"] / frame["identified_people"].replace(0, pd.NA)
    frame["confirmed_rate"] = frame["confirmed_external_registrations"] / frame["external_registrations"].replace(0, pd.NA)

    left, right = st.columns(2)
    with left:
        fig = px.bar(frame.sort_values("cost_per_attendee", na_position="last"),
                     x="cost_per_attendee", y="campaign_name", orientation="h",
                     title="Cost per attributed attendee",
                     labels={"cost_per_attendee": "Cost per attendee (₹)", "campaign_name": ""},
                     color_discrete_sequence=["#315bcb"])
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=390)
        render_chart(fig)
    with right:
        fig = px.bar(frame.sort_values("attributed_attendees"),
                     x="campaign_name", y="attributed_attendees",
                     title="Attributed verified external attendees",
                     labels={"attributed_attendees": "Attendees", "campaign_name": ""},
                     color_discrete_sequence=["#198754"])
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=390)
        render_chart(fig)

    fig = px.scatter(frame, x="spend", y="attributed_attendees", size="external_registrations",
                     color="campaign_name", hover_data=["confirmed_external_registrations", "cost_per_attendee"],
                     title="Spend versus recorded attendee results",
                     labels={"spend": "Spend (₹)", "attributed_attendees": "Attendees"})
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=380)
    render_chart(fig)

    display = frame[[
        "campaign_name", "spend", "identified_people", "external_registrations",
        "confirmed_external_registrations", "attributed_attendees", "registration_rate",
        "confirmed_rate", "confirmed_to_attended", "cost_per_attendee",
    ]].copy()
    display["registration_rate"] *= 100
    display["confirmed_rate"] *= 100
    display["confirmed_to_attended"] *= 100
    display.columns = [
        "Campaign", "Spend", "Identified people", "Registrations", "Confirmed",
        "Attendees", "Registration rate", "Confirmed rate", "Confirmed → attended",
        "Cost / attendee",
    ]
    st.dataframe(
        display.sort_values("Attendees", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "Spend": st.column_config.NumberColumn(format="₹%.0f"),
            "Registration rate": st.column_config.NumberColumn(format="%.1f%%"),
            "Confirmed rate": st.column_config.NumberColumn(format="%.1f%%"),
            "Confirmed → attended": st.column_config.NumberColumn(format="%.1f%%"),
            "Cost / attendee": st.column_config.NumberColumn(format="₹%.2f"),
        },
    )
    efficient = frame.sort_values("cost_per_attendee", na_position="last").iloc[0]
    weak = frame.sort_values("confirmed_to_attended", na_position="last").iloc[0]
    st.markdown(
        f'<div class="insight"><b>Efficient recorded result:</b> {efficient["campaign_name"]} '
        f'was ₹{float(efficient["cost_per_attendee"]):,.2f} per attributed attendee. '
        f'<b>Show-up review:</b> {weak["campaign_name"]} had the lowest confirmed-to-attended rate '
        f'in this view at {format_percent(float(weak["confirmed_to_attended"]))}. '
        f'Campaign attribution is historical and not causal.</div>',
        unsafe_allow_html=True,
    )


def budget_management(kpis: dict[str, object]) -> None:
    st.title("Budget Management")
    st.caption("Planning edits are session-only and do not modify the immutable workbook")
    initialize_state()
    baseline = kpis["baseline"]

    historical_budget = baseline.revised_budget
    budget = effective_budget(historical_budget)
    historical_campaigns = kpis["campaigns"].copy()
    campaign_frame = apply_campaign_spend_edits(historical_campaigns)

    left, right = st.columns(2)
    with left:
        new_budget = st.number_input("Configured marketing budget (₹)", min_value=0.0,
                                     value=float(budget), step=5000.0)
        if new_budget != budget:
            set_total_budget(float(new_budget))
            budget = float(new_budget)
    with right:
        if st.button("Reset all planning edits"):
            reset_budget_state()
            st.session_state.pop("pending_budget_proposal", None)
            st.rerun()

    campaign_spend = float(campaign_frame["spend"].sum())
    remaining = budget - campaign_spend
    utilization = campaign_spend / budget if budget else 0

    metric_grid([
        ("Marketing budget", format_inr(budget), "User-edited planning value" if budget != historical_budget else "Historical revised budget", "navy"),
        ("Campaign spend", format_inr(campaign_spend), "Historical or user-edited", "navy"),
        ("Remaining budget", format_inr(remaining), "May be negative only as an over-budget warning", "red" if remaining < 0 else "green"),
        ("Utilization", format_percent(utilization), "Campaign spend / configured budget", "amber" if utilization > 1 else "navy"),
    ], 2)

    if campaign_spend > budget:
        st.warning("Campaign planning spend exceeds the configured marketing budget. Reduce allocation or confirm a higher budget.")

    st.subheader("Campaign spend planning")
    for row in campaign_frame.itertuples(index=False):
        amount = st.number_input(
            f"{row.campaign_name}",
            min_value=0.0,
            value=float(row.spend),
            step=500.0,
            key=f"spend_{row.campaign_id}",
        )
        if amount != float(row.spend):
            set_campaign_spend(row.campaign_id, float(amount))
            st.rerun()

    st.subheader("Campaign spending")
    fig = px.bar(campaign_frame.sort_values("spend", ascending=False),
                 x="campaign_name", y="spend", text="spend",
                 labels={"campaign_name": "", "spend": "Spend (₹)"},
                 color_discrete_sequence=["#315bcb"])
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380)
    render_chart(fig)


def scenario_lab(kpis: dict[str, object]) -> None:
    st.title("Scenario Lab")
    st.caption("Hypothetical planning values; never presented as observed outcomes")
    baseline = kpis["baseline"]
    current = st.session_state.get("scenario_assumptions") or initial_scenario_assumptions(kpis)

    left, right = st.columns(2)
    with left:
        visitor_target = st.number_input(
            "Visitor target",
            min_value=0,
            value=int(current["visitor_target"]),
            step=50,
            key="scenario_visitor_target",
        )
        registration_conversion = st.slider("Visitor-to-registration conversion", 0.0, 1.0,
                                            float(current["registration_conversion"]), 0.01,
                                            key="scenario_registration_conversion")
        confirmation_rate = st.slider("Confirmation rate", 0.0, 1.0,
                                      float(current["confirmation_rate"]), 0.01,
                                      key="scenario_confirmation_rate")
    with right:
        show_up_rate = st.slider("Registered show-up rate", 0.0, 1.0,
                                 float(current["show_up_rate"]), 0.01,
                                 key="scenario_show_up_rate")
        walk_ins = st.number_input("Walk-ins", min_value=0, value=int(current["walk_ins"]), step=25,
                                   key="scenario_walk_ins")
        marketing_budget = st.number_input("Marketing budget (₹)", min_value=0.0,
                                           value=float(current["marketing_budget"]), step=5000.0,
                                           key="scenario_marketing_budget")

    st.session_state["scenario_assumptions"] = {
        "visitor_target": int(visitor_target),
        "registration_conversion": float(registration_conversion),
        "confirmation_rate": float(confirmation_rate),
        "show_up_rate": float(show_up_rate),
        "walk_ins": int(walk_ins),
        "marketing_budget": float(marketing_budget),
    }

    try:
        outputs = calculate_scenario(ScenarioInputs(
            visitor_target=int(visitor_target),
            registration_conversion=float(registration_conversion),
            confirmation_rate=float(confirmation_rate),
            show_up_rate=float(show_up_rate),
            walk_ins=int(walk_ins),
            marketing_budget=float(marketing_budget),
        ))
    except ValueError as exc:
        st.error(str(exc))
        return

    metric_grid([
        ("Projected registrations", f"{outputs.projected_registrations:,}", "Hypothetical", "navy"),
        ("Projected confirmed", f"{outputs.projected_confirmed:,}", "Hypothetical", "green"),
        ("Projected registered attendees", f"{outputs.projected_registered_attendees:,}", "Hypothetical", "green"),
        ("Projected walk-ins", f"{outputs.projected_walk_ins:,}", "Hypothetical", "amber"),
        ("Projected total attendees", f"{outputs.projected_total_attendees:,}", "Hypothetical", "navy"),
        ("Projected cost / attendee", format_inr(outputs.projected_cost_per_attendee), "Hypothetical", "navy"),
        ("Target achievement", format_percent(outputs.target_achievement), "Projected attendees / visitor target", "green" if outputs.target_achievement >= 1 else "amber"),
    ], 3)

    base = [
        baseline.external_registrations,
        baseline.confirmed_external_registrations,
        baseline.registered_attendees,
        baseline.walk_in_attendees,
        baseline.unique_external_attendees,
    ]
    modified = [
        outputs.projected_registrations,
        outputs.projected_confirmed,
        outputs.projected_registered_attendees,
        outputs.projected_walk_ins,
        outputs.projected_total_attendees,
    ]
    labels = ["Registrations", "Confirmed", "Registered", "Walk-ins", "Total attendees"]
    comparison = pd.DataFrame({
        "Stage": labels,
        "Historical base": base,
        "Modified scenario": modified,
    })
    fig = px.bar(comparison, x="Stage", y=["Historical base", "Modified scenario"], barmode="group")
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380)
    render_chart(fig)


def analyst_chat(kpis: dict[str, object]) -> None:
    st.title("AI Growth Analyst")
    st.caption("Grounded answers from the shared RISA analytics. Hypotheticals and planning edits are clearly separated from historical results.")
    context = build_context(load_phase0(), kpis, st.session_state)
    provider, provider_notice = configured_provider()
    if provider is None:
        st.info(provider_notice or "Using deterministic local analyst mode.")
    elif provider_notice:
        st.warning(provider_notice)

    if "analyst_messages" not in st.session_state:
        st.session_state["analyst_messages"] = []

    _, top_right = st.columns([5, 1])
    with top_right:
        if st.button("New chat", use_container_width=True):
            st.session_state["analyst_messages"] = []
            st.session_state.pop("pending_budget_proposal", None)
            st.session_state.pop("analyst_next_prompt", None)
            st.rerun()

    for item in st.session_state["analyst_messages"]:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("tools_used"):
                st.caption("Data checked: " + ", ".join(item["tools_used"]))

    proposal = st.session_state.get("pending_budget_proposal")
    if proposal:
        with st.container(border=True):
            st.subheader("Budget reallocation proposal — awaiting confirmation")
            st.markdown(
                f"Move **₹{proposal['amount']:,.0f}** from **{proposal['source_campaign']}** "
                f"(₹{proposal['source_before']:,.0f} → ₹{proposal['source_after']:,.0f}) "
                f"to **{proposal['destination_campaign']}** "
                f"(₹{proposal['destination_before']:,.0f} → ₹{proposal['destination_after']:,.0f})."
            )
            st.caption(f"Reason: {proposal['reason']}")
            st.caption(
                f"Risk: {proposal['risk']} Measurement: {proposal['measurement']}"
            )
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm this transfer", type="primary", use_container_width=True):
                    try:
                        apply_confirmed_proposal(context, proposal)
                    except (ValueError, KeyError) as exc:
                        st.error(f"Could not apply proposal: {exc}")
                    else:
                        st.session_state.pop("pending_budget_proposal", None)
                        st.session_state["analyst_messages"].append({
                            "role": "assistant",
                            "content": (
                                f"Confirmed. Planning spend moved: {proposal['source_campaign']} is now "
                                f"₹{proposal['source_after']:,.0f}; {proposal['destination_campaign']} is now "
                                f"₹{proposal['destination_after']:,.0f}. Historical workbook values remain unchanged."
                            ),
                            "tools_used": ["get_budget_status"],
                        })
                        st.session_state["analyst_messages"] = st.session_state["analyst_messages"][-40:]
                        st.rerun()
            with cancel_col:
                if st.button("Cancel proposal", use_container_width=True):
                    st.session_state.pop("pending_budget_proposal", None)
                    st.rerun()

    if not st.session_state["analyst_messages"]:
        st.markdown("**Try asking**")
        prompts = [
            "What is our biggest growth problem?",
            "Which campaign should we prioritize?",
            "How much budget is left?",
            "What if our show rate increases to 85%?",
        ]
        prompt_columns = st.columns(2)
        for index, prompt_text in enumerate(prompts):
            with prompt_columns[index % 2]:
                if st.button(prompt_text, use_container_width=True):
                    st.session_state["analyst_next_prompt"] = prompt_text
                    st.rerun()

    typed_prompt = st.chat_input("Ask about attendees, campaigns, budget, or a scenario")
    prompt = typed_prompt or st.session_state.pop("analyst_next_prompt", None)
    if prompt:
        history = list(st.session_state["analyst_messages"])
        st.session_state["analyst_messages"].append({"role": "user", "content": prompt})
        pending = st.session_state.get("pending_budget_proposal")
        if is_explicit_proposal_confirmation(prompt, pending):
            try:
                apply_confirmed_proposal(context, pending)
            except (ValueError, KeyError) as exc:
                confirmation_text = f"Could not apply the proposal: {exc} No planning values were changed."
            else:
                confirmation_text = (
                    f"Confirmed. Planning spend moved: {pending['source_campaign']} is now "
                    f"₹{pending['source_after']:,.0f}; {pending['destination_campaign']} is now "
                    f"₹{pending['destination_after']:,.0f}. Historical workbook values remain unchanged."
                )
            st.session_state.pop("pending_budget_proposal", None)
            st.session_state["analyst_messages"].append({
                "role": "assistant",
                "content": confirmation_text,
                "tools_used": ["get_budget_status"],
            })
            st.session_state["analyst_messages"] = st.session_state["analyst_messages"][-40:]
            st.rerun()
        with st.spinner("Analyzing current RISA data..."):
            reply = answer_question(
                prompt,
                context,
                history,
                provider,
                st.session_state.get("pending_budget_proposal"),
            )
        st.session_state["analyst_messages"].append({
            "role": "assistant",
            "content": reply.text,
            "tools_used": reply.tools_used,
        })
        st.session_state["analyst_messages"] = st.session_state["analyst_messages"][-40:]
        if reply.pending_proposal:
            st.session_state["pending_budget_proposal"] = reply.pending_proposal
        if prompt.strip().casefold() in {"cancel", "cancel proposal", "reject it", "reject proposal"}:
            st.session_state.pop("pending_budget_proposal", None)
        if any(phrase in prompt.casefold() for phrase in (
            "reset planning edits",
            "reset budget edits",
            "reset proposed edits",
            "reset the proposed edits",
            "restore original planning",
        )):
            st.session_state.pop("pending_budget_proposal", None)
        if reply.provider_error:
            st.warning(f"AI provider unavailable; answered with local analyst mode. {reply.provider_error}")
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="RISA Growth Center", page_icon="R", layout="wide")
    apply_page_style()
    initialize_state()

    st.sidebar.markdown(
        """
        <div style="padding: 8px 10px 14px 10px;">
          <div style="font-size: 1.18rem; font-weight: 750; color: #20283a; letter-spacing: -0.03em;">RISA</div>
          <div style="font-size: 0.76rem; color: #8791a1; margin-top: 3px;">Festival Growth Center</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.sidebar.radio(
        "Navigation",
        [
            "Command Center",
            "Funnel Analysis",
            "Campaign Performance",
            "Budget Management",
            "Scenario Lab",
            "AI Growth Analyst",
        ],
    )

    kpis = load_kpis()
    if "scenario_assumptions" not in st.session_state:
        st.session_state["scenario_assumptions"] = initial_scenario_assumptions(kpis)
    if page == "Command Center":
        command_center(kpis)
    elif page == "Funnel Analysis":
        funnel_analysis(kpis)
    elif page == "Campaign Performance":
        campaign_performance(kpis)
    elif page == "Budget Management":
        budget_management(kpis)
    elif page == "Scenario Lab":
        scenario_lab(kpis)
    else:
        analyst_chat(kpis)


if __name__ == "__main__":
    main()
