import pandas as pd
from pymongo import MongoClient
from config import MONGO_CONFIG

# =====================================================
# CONNECT MONGODB
# =====================================================

client = MongoClient(MONGO_CONFIG["uri"])
db = client[MONGO_CONFIG["database"]]

print("Connected to MongoDB!")

# =====================================================
# LOAD DATA
# =====================================================

flights = pd.read_csv("data/airline_delay.csv")
states = pd.read_csv("data/states.csv")

flights.columns = flights.columns.str.lower()

print("CSV files loaded!")

# =====================================================
# CLEAN
# =====================================================

flights = flights.fillna(0)

# =====================================================
# REGION mapping (from states)
# =====================================================

states.columns = ["state_name", "state_code", "region", "division"]

state_region_map = states[["state_code", "region"]].drop_duplicates()

flights["state_code"] = flights["airport_name"].str.extract(r",\s([A-Z]{2}):")
flights = flights.merge(state_region_map, on="state_code", how="left")

# =====================================================
# 1. delay_time_analysis 
# =====================================================

delay_time = flights.groupby(["year", "month", "region"]).agg(
    total_flights=("arr_flights", "sum"),
    total_delay_flights=("arr_del15", "sum"),
    weather_delay_count=("weather_ct", "sum"),
    weather_delay_duration=("weather_delay", "sum")
).reset_index()

delay_time["weather_delay_percentage_total"] = (
    delay_time["weather_delay_count"] /
    delay_time["total_flights"] * 100
)

delay_time["weather_risk_share"] = (
    delay_time["weather_delay_count"] /
    delay_time["total_delay_flights"] * 100
)

delay_time["avg_delay"] = (
    delay_time["weather_delay_duration"] /
    delay_time["weather_delay_count"]
)

q_low = delay_time["weather_delay_percentage_total"].quantile(0.33)
q_high = delay_time["weather_delay_percentage_total"].quantile(0.66)

def classify_risk(x):
    if x <= q_low:
        return "Low"
    elif x <= q_high:
        return "Medium"
    else:
        return "High"

delay_time["risk_level"] = delay_time["weather_delay_percentage_total"].apply(classify_risk)

db.delay_time_analysis.delete_many({})
db.delay_time_analysis.insert_many(delay_time.to_dict("records"))

print("Inserted delay_time_analysis")

# =====================================================
# 2. airline_performance 
# =====================================================

airline_perf = flights.groupby(
    ["year", "month", "carrier", "carrier_name"]
).agg(
    total_flights=("arr_flights", "sum"),
    total_delay_flights=("arr_del15", "sum"),
    avg_delay=("arr_delay", "mean")
).reset_index()

airline_perf["delay_percentage"] = (
    airline_perf["total_delay_flights"] /
    airline_perf["total_flights"] * 100
)

airline_perf["rank"] = airline_perf.groupby(
    ["year", "month"]
)["delay_percentage"].rank(method="dense", ascending=False)

db.airline_performance.delete_many({})
db.airline_performance.insert_many(airline_perf.to_dict("records"))

print("Inserted airline_performance")

# =====================================================
# 3. delay_cause_distribution 
# =====================================================

delay_cause = flights.groupby(["year", "month", "region"]).agg(
    carrier_ct=("carrier_ct", "sum"),
    weather_ct=("weather_ct", "sum"),
    nas_ct=("nas_ct", "sum"),
    security_ct=("security_ct", "sum"),
    late_aircraft_ct=("late_aircraft_ct", "sum"),

    carrier_delay=("carrier_delay", "sum"),
    weather_delay=("weather_delay", "sum"),
    nas_delay=("nas_delay", "sum"),
    security_delay=("security_delay", "sum"),
    late_aircraft_delay=("late_aircraft_delay", "sum")
).reset_index()

ct_cols = ["carrier_ct","weather_ct","nas_ct","security_ct","late_aircraft_ct"]
delay_cols = ["carrier_delay","weather_delay","nas_delay","security_delay","late_aircraft_delay"]

delay_cause["dominant_by_ct"] = delay_cause[ct_cols].idxmax(axis=1)
delay_cause["dominant_by_delay"] = delay_cause[delay_cols].idxmax(axis=1)

db.delay_cause_distribution.delete_many({})
db.delay_cause_distribution.insert_many(delay_cause.to_dict("records"))

print("Inserted delay_cause_distribution")

print("===================================")
print("ALL MONGODB DATA IMPORTED")
