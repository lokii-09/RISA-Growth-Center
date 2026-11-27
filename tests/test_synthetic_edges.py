import pandas as pd

from src.analytics.attendance import attendance_by_day, valid_external_attendance
from src.analytics.funnel import latest_registration_status
from src.models import CanonicalDataset


def synthetic_dataset():
    people = pd.DataFrame([
        {"person_id": "P1", "person_type": "external"},
        {"person_id": "P2", "person_type": "internal"},
    ])
    checkins = pd.DataFrame([
        {"event_id": "E1", "person_id": "P1", "occurred_at": pd.Timestamp("2025-04-12 10:00"), "result": "admitted", "verification": "verified", "registration_id": "R1"},
        {"event_id": "E2", "person_id": "P1", "occurred_at": pd.Timestamp("2025-04-12 11:00"), "result": "admitted", "verification": "verified", "registration_id": "R1"},
        {"event_id": "E3", "person_id": "P1", "occurred_at": pd.Timestamp("2025-04-13 10:00"), "result": "denied", "verification": "verified", "registration_id": "R1"},
        {"event_id": "E4", "person_id": "P2", "occurred_at": pd.Timestamp("2025-04-12 10:00"), "result": "admitted", "verification": "verified", "registration_id": None},
    ])
    history = pd.DataFrame([
        {"history_id": "H1", "registration_id": "R1", "effective_at": pd.Timestamp("2025-04-10"), "status": "interested"},
        {"history_id": "H2", "registration_id": "R1", "effective_at": pd.Timestamp("2025-04-11"), "status": "confirmed"},
        {"history_id": "H3", "registration_id": "R1", "effective_at": pd.Timestamp("2025-04-14"), "status": "cancelled"},
    ])
    return CanonicalDataset(
        original={"People": people, "Check-ins": checkins, "Registration History": history},
        working={"People": people, "Check-ins": checkins, "Registration History": history},
    )


def test_synthetic_duplicate_checkins_count_one_person():
    dataset = synthetic_dataset()
    valid, attendees = valid_external_attendance(dataset, pd.Timestamp("2025-04-13 20:00"))
    assert attendees == {"P1"}
    assert len(valid) == 2
    assert attendance_by_day(valid) == {"2025-04-12": 1}


def test_synthetic_as_of_status_excludes_future_history():
    dataset = synthetic_dataset()
    latest = latest_registration_status(dataset, pd.Timestamp("2025-04-13 20:00"))
    assert latest.iloc[0]["status"] == "confirmed"
