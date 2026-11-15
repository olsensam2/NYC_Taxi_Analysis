from pathlib import Path
from urllib.request import urlretrieve

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


months = []
for year in [2024, 2025, 2026]:
    for month in range(1, 13):
        if year == 2024 and month < 10:
            continue
        if year == 2026 and month > 9:
            continue
        month_str = f"{year}-{month:02d}"
        months.append(month_str)
        

for m in months:
    url = BASE_URL.format(month=m)
    target = RAW_DIR / f"yellow_tripdata_{m}.parquet"

    if target.exists():
        print(f"skip {target.name}")
        continue

    try:
        urlretrieve(url, target)
        print(f"ok {target.name}")
    except Exception as e:
        print(f"FAILED {target.name}, {e}")



zone_target = RAW_DIR / "taxi_zone_lookup.csv"

if zone_target.exists():
    print(f"skip {zone_target.name}")
else:
    try:
        urlretrieve(ZONE_URL, zone_target)
        print(f"ok {zone_target.name}")
    except Exception as e:
        print(f"FAILED {zone_target.name}, {e}")


