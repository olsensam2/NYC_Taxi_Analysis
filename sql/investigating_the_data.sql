select 
	 Borough
	,count(*)
from 'data/raw/yellow_tripdata_*.parquet' t
left join 'data/raw/taxi_zone_lookup.csv' z
on t.PULocationID = z.LocationID
group by Borough
order by count(*) DESC;

--return the full rows where Borough is 'unknown' or 'N/A'
select 
	 *
from 'data/raw/taxi_zone_lookup.csv' 
where borough IN ('Unknown', 'N/A');

--count the rows where the borough is null
select 
	count(*)
from 'data/raw/taxi_zone_lookup.csv' 
where borough IS NULL;

--cardinality of key code columns
select 
	 count(distinct(PULocationID))
	,count(distinct(DOLocationID))
	,count(distinct(VendorID))
	,count(distinct(payment_type))
	,count(distinct(RatecodeID))
from 'data/raw/yellow_tripdata_*.parquet';

--average per month
select 
	count(*) / count(distinct(filename)) AS avg_trips_per_month
from 'data/raw/yellow_tripdata_*.parquet';