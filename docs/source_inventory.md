# Source inventory: NYC TLC yellow taxi trip records

| | |
|---|---|
| **Owner** | Sam Olsen |
| **Inventory date** | 2026-11-16 |
| **Status** | Raw files landed and profiled at file level. Column-level profiling not yet done. |
| **Tooling** | DuckDB 2.0.0 (CLI), Python 3.12 |
| **Reproduce** | `python src/download_data.py`, then the queries in the appendix |

## 1. Summary

Two years of NYC yellow taxi trips (October 2024 to September 2026): 93.45 million rows in 24 monthly Parquet files, plus a 265-row zone lookup CSV. One row is one trip. There is no trip ID, the schema changes once inside the window, and the zone lookup uses placeholder strings instead of NULLs. All three are covered under Known issues.

## 2. Source

| | |
|---|---|
| **Publisher** | NYC Taxi and Limousine Commission (TLC) |
| **Collected by** | Technology vendors authorized under the Taxicab Passenger Enhancement Program (TPEP), then submitted to TLC |
| **Accuracy** | TLC states it did not create the data and does not vouch for its accuracy. Treat every field as vendor-reported. |
| **Publication cadence** | Monthly, typically about two months behind |
| **Latest month available** | September 2026 (checked 2026-11-14) |
| **Documentation** | Data dictionary PDF on the TLC Trip Record Data page, under "Data Dictionaries and MetaData" |
| **Access** | Public download over HTTPS, no credentials |

## 3. Files

| Dataset | Format | Files | Naming | Location |
|---|---|---|---|---|
| Yellow taxi trips | Parquet | 24 | `yellow_tripdata_YYYY-MM.parquet` | `data/raw/` |
| Taxi zone lookup | CSV | 1 | `taxi_zone_lookup.csv` | `data/raw/` |

- **Coverage:** 2024-10 through 2026-09, one file per month, no gaps.
- **Size:** about 1.6 GB in total; 56 to 74 MB per trip file; the lookup is 12 KB.
- **Version control:** `data/raw/` is ignored by Git. The files are rebuilt from source by `src/download_data.py`.
- **Ingestion:** the script is idempotent. It skips any file already present and reports `ok`, `skip` or `FAILED` per file, so it is safe to re-run.

## 4. Volume

| Measure | Value |
|---|---|
| Total rows | 93,450,512 |
| Average per month | 3,893,771 |
| Smallest month | 2026-08: 3,336,716 |
| Largest month | 2025-05: 4,591,845 |

Rows per file:

| Month | Rows | Month | Rows |
|---|---|---|---|
| 2024-10 | 3,833,771 | 2025-10 | 4,428,699 |
| 2024-11 | 3,646,369 | 2025-11 | 4,181,444 |
| 2024-12 | 3,668,371 | 2025-12 | 4,305,006 |
| 2025-01 | 3,475,226 | 2026-01 | 3,724,889 |
| 2025-02 | 3,577,543 | 2026-02 | 3,399,866 |
| 2025-03 | 4,145,257 | 2026-03 | 3,952,451 |
| 2025-04 | 3,970,553 | 2026-04 | 3,831,240 |
| 2025-05 | 4,591,845 | 2026-05 | 4,090,836 |
| 2025-06 | 4,322,960 | 2026-06 | 3,837,248 |
| 2025-07 | 3,898,963 | 2026-07 | 3,530,109 |
| 2025-08 | 3,574,091 | 2026-08 | 3,336,716 |
| 2025-09 | 4,251,015 | 2026-09 | 3,876,044 |

## 5. Schema

### Trips

19 columns in the 2024 files, 20 from 2025 onwards.

| Group | Columns |
|---|---|
| Vendor and codes | `VendorID`, `RatecodeID`, `store_and_fwd_flag`, `payment_type` |
| Time | `tpep_pickup_datetime`, `tpep_dropoff_datetime` |
| Trip | `passenger_count`, `trip_distance` |
| Location | `PULocationID`, `DOLocationID` |
| Money | `fare_amount`, `extra`, `mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`, `total_amount`, `congestion_surcharge`, `Airport_fee` |
| Added in 2025 | `cbd_congestion_fee` (double), last column in the file |

### Zone lookup

| Column | Type | Notes |
|---|---|---|
| `LocationID` | int64 | Unique. 265 values. |
| `Borough` | varchar | Five boroughs plus `EWR`, `Unknown` and `N/A` |
| `Zone` | varchar | Zone name |
| `service_zone` | varchar | For example `Yellow Zone`, `Boro Zone`, `EWR` |

## 6. Grain and keys

- **Grain:** one row per taxi trip.
- **Primary key (trips):** none. The source has no trip ID. A candidate composite key (vendor, pickup time, dropoff time, pickup and dropoff location) has **not yet been tested** for uniqueness.
- **Primary key (lookup):** `LocationID`. Verified: 265 rows, 265 distinct values.
- **Relationship:** zone lookup to trips is one-to-many, on `LocationID` = `PULocationID` (and separately on `DOLocationID`). The lookup is a role-playing dimension: pickup zone and dropoff zone.
- **Referential integrity:** verified for pickups. A LEFT JOIN from trips to the lookup returns 93,450,512 rows (no fan-out) and no NULL borough (no orphan `PULocationID`). Not yet checked for `DOLocationID`.

## 7. Cardinality

| Column | Distinct non-NULL values | Notes |
|---|---|---|
| `PULocationID` | 263 | 2 of the 265 lookup zones have no pickups in the window |
| `DOLocationID` | 263 | 2 zones have no dropoffs; not confirmed to be the same 2 |
| `VendorID` | 4 | Not yet checked against the data dictionary |
| `payment_type` | 6 | Not yet checked against the data dictionary |
| `RatecodeID` | 7 | Not yet checked against the data dictionary |

Pickups by borough (all 24 months):

| Borough | Trips | Share |
|---|---|---|
| Manhattan | 80,765,249 | 86.4% |
| Queens | 8,655,130 | 9.3% |
| Brooklyn | 3,152,854 | 3.4% |
| Bronx | 662,952 | 0.7% |
| Unknown | 148,722 | 0.16% |
| N/A (Outside of NYC) | 44,638 | 0.05% |
| EWR (Newark Airport) | 12,230 | 0.01% |
| Staten Island | 8,737 | 0.01% |

## 8. Known issues

| # | Issue | Evidence | Impact | Handling |
|---|---|---|---|---|
| 1 | **Schema drift.** `cbd_congestion_fee` exists only from 2025. | 19 vs 20 columns in `DESCRIBE`. Selecting the column across all files errors with default settings. | Any query or load that names the column fails across the full window. | Read with `union_by_name = true`. |
| 2 | **NULL, not zero, before 2025.** | With `union_by_name`, the three 2024 files have 0 non-NULL values; every later file is fully populated. | `SUM` skips the NULLs, but `AVG` and row-level arithmetic (`total - fee`) behave differently for 2024. | Decide in the cleaned layer whether "fee did not exist" should stay NULL or become 0. Document the choice. |
| 3 | **No trip ID.** | No identifier column in the schema. | Duplicates cannot be detected by key; row-level lineage is not possible. | Test a composite candidate key; add a surrogate key in the cleaned layer. |
| 4 | **Placeholder strings in the zone lookup.** | `LocationID` 264 has Borough `Unknown`; 265 has Borough `N/A` and Zone `Outside of NYC`. `Borough IS NULL` returns 0 rows. | A NULL check reports no missing locations, while 193,360 pickups (0.21%) have no usable borough. | Do not edit the raw file. The two rows mean different things: 264 is unknown, 265 is a known category (outside the city). Map them explicitly in the cleaned layer. |
| 5 | **Non-borough value `EWR`.** | `LocationID` 1, Newark Airport, New Jersey. | Borough-level reports show eight categories, not five. | Keep as its own category; label it clearly in reports. |
| 6 | **Inconsistent column naming.** | Mixed styles: `VendorID`, `RatecodeID`, `PULocationID`; `tpep_pickup_datetime`, `fare_amount`; `Airport_fee` with a capital A beside `cbd_congestion_fee`. | Typos and case-sensitivity errors in engines that are case-sensitive. | Rename to snake_case in the cleaned layer. |
| 7 | **Vendor-reported, unaudited data.** | TLC disclaimer. | Expect invalid values (zero distances, negative fares, out-of-window dates). Not yet measured. | Column-level profiling next. |

## 9. Open items

- Column-level profiling: NULL rates, ranges, invalid and out-of-window values.
- Test the composite candidate key for uniqueness.
- Identify the two zones with no pickups and the two with no dropoffs.
- Check `VendorID`, `payment_type` and `RatecodeID` values against the data dictionary.
- Check `DOLocationID` referential integrity against the lookup.
- Record column data types for the trips table.

## Appendix: queries

Run in the DuckDB CLI from the repository root.

```sql
-- Rows per file
SELECT filename, count(*) AS trips
FROM 'data/raw/yellow_tripdata_*.parquet'
GROUP BY filename
ORDER BY filename;

-- Volume summary without a hard-coded file count
SELECT avg(trips) AS avg_per_month, min(trips) AS smallest, max(trips) AS largest
FROM (
    SELECT filename, count(*) AS trips
    FROM 'data/raw/yellow_tripdata_*.parquet'
    GROUP BY filename
);

-- Schema drift: non-NULL cbd_congestion_fee per file
SELECT filename, count(*) AS trips, count(cbd_congestion_fee) AS fee_populated
FROM read_parquet('data/raw/yellow_tripdata_*.parquet', union_by_name = true)
GROUP BY filename
ORDER BY filename;

-- Lookup key check
SELECT count(*) AS zone_rows, count(DISTINCT LocationID) AS distinct_ids
FROM 'data/raw/taxi_zone_lookup.csv';

-- Fan-out and orphan check, pickups by borough
SELECT z.Borough, count(*) AS trips
FROM 'data/raw/yellow_tripdata_*.parquet' t
LEFT JOIN 'data/raw/taxi_zone_lookup.csv' z
    ON t.PULocationID = z.LocationID
GROUP BY z.Borough
ORDER BY trips DESC;

-- Cardinality of code and key columns
SELECT
    count(DISTINCT PULocationID) AS pu_zones,
    count(DISTINCT DOLocationID) AS do_zones,
    count(DISTINCT VendorID)     AS vendors,
    count(DISTINCT payment_type) AS payment_types,
    count(DISTINCT RatecodeID)   AS rate_codes
FROM 'data/raw/yellow_tripdata_*.parquet';
```
