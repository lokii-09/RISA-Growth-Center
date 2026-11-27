# Phase 0 Data Quality Report

## Raw and cleaned record counts

| Table | Raw records | Clean records |
|---|---:|---:|
| Event | 1 | 1 |
| Targets | 2 | 2 |
| Campaigns | 7 | 7 |
| Daily Marketing | 483 | 481 |
| People | 3685 | 3685 |
| Interest and Engagement | 11650 | 11650 |
| Registrations | 2840 | 2840 |
| Registration History | 5911 | 5907 |
| Check-ins | 3390 | 3370 |
| Read me | 8 | 8 |
| Field guide | 86 | 86 |

## Missing values retained in the source copy

| Table | Field | Missing values |
|---|---|---:|
| People | first_campaign_name | 145 |
| People | first_campaign_id | 145 |
| Check-ins | campaign_name | 170 |
| Check-ins | registration_id | 170 |
| Check-ins | campaign_id | 170 |

Missing values are reported rather than silently removed; whether a blank is valid depends on the field.

## Cleaning decisions and issues

| Table | Issue | Count | Stable ID | Details |
|---|---|---:|---|---|
| Daily Marketing | duplicate_stable_id_rows | 4 | activity_id | 2 exact groups (2 extra rows); 0 conflicting groups (0 extra rows). Kept the first row per ID; rows without an ID were preserved. |
| Registration History | duplicate_stable_id_rows | 8 | history_id | 4 exact groups (4 extra rows); 0 conflicting groups (0 extra rows). Kept the first row per ID; rows without an ID were preserved. |
| Check-ins | duplicate_stable_id_rows | 40 | event_id | 20 exact groups (20 extra rows); 0 conflicting groups (0 extra rows). Kept the first row per ID; rows without an ID were preserved. |

## Stable duplicate handling

Exact rows with duplicate stable IDs are deduplicated with `keep='first'` in the working copy.
Conflicting copies are also reported and retain the first source row deterministically; they are not merged.
Rows with missing stable IDs are preserved and reported. The original DataFrames remain unchanged.
Nonblank source values that fail date or numeric conversion are reported as issues and represented as missing in the typed working copy.
