from __future__ import annotations

import pandas as pd

from ..models import CanonicalDataset
from .attendance import valid_external_attendance
from .budget import campaign_spend
from .funnel import external_people, latest_registration_status


def campaign_metrics(dataset: CanonicalDataset, as_of: pd.Timestamp) -> pd.DataFrame:
    campaigns = dataset.working["Campaigns"]
    registrations = dataset.working["Registrations"]
    daily = dataset.working["Daily Marketing"]
    people = dataset.working["People"]
    external_ids = external_people(dataset)
    latest = latest_registration_status(dataset, as_of)
    confirmed_ids = set(latest.loc[latest["status"].eq("confirmed"), "registration_id"].dropna())
    valid_checkins, _ = valid_external_attendance(dataset, as_of)

    rows: list[dict[str, object]] = []
    for campaign in campaigns.itertuples(index=False):
        campaign_id = campaign.campaign_id
        campaign_regs = registrations[
            registrations["campaign_id"].eq(campaign_id)
            & registrations["person_id"].isin(external_ids)
            & registrations["registered_at"].le(as_of)
        ]
        registration_ids = set(campaign_regs["registration_id"].dropna())
        confirmed_count = len(registration_ids & confirmed_ids)

        recorded_person_ids = set(campaign_regs["person_id"].dropna())
        campaign_attendees = set(
            valid_checkins.loc[
                valid_checkins["person_id"].isin(recorded_person_ids),
                "person_id",
            ].dropna()
        )

        identified_people = int(
            people[
                people["person_type"].eq("external")
                & people["first_campaign_id"].eq(campaign_id)
            ]["person_id"].nunique()
        )
        if daily is not None:
            daily_rows = daily[
                daily["campaign_id"].eq(campaign_id)
                & daily["activity_date"].le(as_of.normalize())
            ]
            clicks = int(pd.to_numeric(daily_rows["clicks"], errors="coerce").fillna(0).sum())
            sessions = int(pd.to_numeric(daily_rows["landing_page_sessions"], errors="coerce").fillna(0).sum())
        else:
            clicks = sessions = 0

        spend = campaign_spend(dataset, as_of, campaign_id)
        attendees = len(campaign_attendees)
        rows.append({
            "campaign_id": campaign_id,
            "campaign_name": campaign.campaign_name,
            "spend": spend,
            "identified_people": identified_people,
            "clicks": clicks,
            "landing_page_sessions": sessions,
            "external_registrations": len(registration_ids),
            "confirmed_external_registrations": confirmed_count,
            "attributed_attendees": attendees,
            "confirmed_to_attended": confirmed_count and attendees / confirmed_count,
            "cost_per_attendee": spend / attendees if attendees else None,
        })
    return pd.DataFrame(rows)
